from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.common.json_repair import parse_and_repair_json
from app.common.prompt_builder import build_full_prompt
from app.common.schemas import MEMORY_UPDATE_SCHEMA, CONSISTENCY_CHECK_SCHEMA
from app.common.retry import llm_retry
from app.config.settings import settings
from app.domain.entities import MemoryUpdateResult
from app.infra.db.models.analysis import ChapterAnalysis
from app.infra.db.models.analysis_details import (
    ChapterCharacterMention,
    ChapterEmotionArc,
    ChapterEvent,
    ChapterWorldDelta,
)
from app.infra.db.models.chapter import Chapter
from app.infra.db.models.memory import (
    Character,
    CharacterRelation,
    CharacterState,
    ConsistencyIssue,
    Faction,
    FactionRelation,
    MemoryClaim,
    RealmSystem,
    TimelineEvent,
    WorldSetting,
)
from app.llm.gateway import LLMGateway, LLMRequest

logger = logging.getLogger(__name__)


class MemoryCenterService:
    """Manages long-term memory for a novel: characters, factions,
    world settings, realm systems, timeline events, and consistency checks.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = LLMGateway()

    # ------------------------------------------------------------------
    # Queries (fast, no LLM)
    # ------------------------------------------------------------------

    def get_characters(self, novel_id: int) -> list[Character]:
        return (
            self.db.query(Character)
            .filter(Character.novel_id == novel_id)
            .order_by(Character.name)
            .all()
        )

    def get_character(self, novel_id: int, character_name: str) -> Character | None:
        return self._match_character_name(
            character_name,
            self.db.query(Character)
            .filter(Character.novel_id == novel_id)
            .all(),
        )

    def get_character_states(self, character_id: int) -> list[CharacterState]:
        return (
            self.db.query(CharacterState)
            .filter(CharacterState.character_id == character_id)
            .order_by(CharacterState.created_at.asc())
            .all()
        )

    def get_character_relations(self, novel_id: int) -> list[CharacterRelation]:
        return (
            self.db.query(CharacterRelation)
            .filter(CharacterRelation.novel_id == novel_id)
            .all()
        )

    def get_factions(self, novel_id: int) -> list[Faction]:
        return (
            self.db.query(Faction)
            .filter(Faction.novel_id == novel_id)
            .order_by(Faction.name)
            .all()
        )

    def get_world_settings(self, novel_id: int, category: str | None = None) -> list[WorldSetting]:
        q = self.db.query(WorldSetting).filter(WorldSetting.novel_id == novel_id)
        if category:
            q = q.filter(WorldSetting.category == category)
        return q.order_by(WorldSetting.category, WorldSetting.name).all()

    def get_realm_systems(self, novel_id: int) -> list[RealmSystem]:
        return (
            self.db.query(RealmSystem)
            .filter(RealmSystem.novel_id == novel_id)
            .all()
        )

    def get_timeline(self, novel_id: int) -> list[TimelineEvent]:
        return (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.novel_id == novel_id)
            .order_by(TimelineEvent.event_order.asc())
            .all()
        )

    def get_consistency_issues(
        self, novel_id: int, status: str | None = None
    ) -> list[ConsistencyIssue]:
        q = self.db.query(ConsistencyIssue).filter(
            ConsistencyIssue.novel_id == novel_id
        )
        if status:
            q = q.filter(ConsistencyIssue.resolution_status == status)
        return q.order_by(ConsistencyIssue.severity.desc()).all()

    # ------------------------------------------------------------------
    # Context Building (used by analysis service)
    # ------------------------------------------------------------------

    def build_character_context(self, novel_id: int) -> str:
        """Return a summary of all known characters for context injection."""
        characters = self.get_characters(novel_id)
        if not characters:
            return '暂无已知角色信息。'

        lines = ['已知角色列表:']
        for c in characters[:20]:  # Limit to 20 most recent
            lines.append(f'- {c.name}（{c.role or "未知定位"}）: {c.summary or "暂无摘要"}')
        return '\n'.join(lines)

    def build_world_context(self, novel_id: int) -> str:
        """Return a summary of known world settings."""
        settings_list = self.get_world_settings(novel_id)
        factions = self.get_factions(novel_id)
        realms = self.get_realm_systems(novel_id)

        parts: list[str] = []

        if factions:
            parts.append('已知势力:')
            for f in factions:
                parts.append(f'- {f.name}（{f.type or "未知类型"}）: {f.description or ""}')

        if settings_list:
            parts.append('已知世界观设定:')
            for s in settings_list[:15]:
                parts.append(f'- [{s.category}] {s.name}: {s.description[:100]}')

        if realms:
            parts.append('已知境界体系:')
            for r in realms:
                parts.append(f'- {r.system_name}')

        return '\n'.join(parts) if parts else '暂无已知世界观信息。'

    def build_recent_context(
        self, novel_id: int, chapter_no: int, count: int = 3
    ) -> str:
        """Return summaries of the last `count` chapters before chapter_no."""
        from app.infra.db.models.chapter import Chapter as ChapterModel

        prev_chapters = (
            self.db.query(ChapterModel)
            .filter(
                ChapterModel.novel_id == novel_id,
                ChapterModel.chapter_no < chapter_no,
            )
            .order_by(ChapterModel.chapter_no.desc())
            .limit(count)
            .all()
        )

        if not prev_chapters:
            return ''

        lines = ['前文章节摘要:']
        for ch in reversed(prev_chapters):
            analysis = (
                self.db.query(ChapterAnalysis)
                .filter(ChapterAnalysis.chapter_id == ch.id)
                .one_or_none()
            )
            summary = analysis.summary if analysis else '（未分析）'
            lines.append(f'- 第{ch.chapter_no}章 {ch.title}: {summary[:150]}')

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Memory Updates (LLM-powered)
    # ------------------------------------------------------------------

    def update_from_analysis(
        self,
        chapter: Chapter,
        analysis_result: dict,
        provider_name: str,
        model_name: str,
    ) -> MemoryUpdateResult:
        """Extract new facts from analysis and update long-term memory tables."""
        result = MemoryUpdateResult()

        # 1. Persist analysis detail records (non-LLM, from the aggregated dict)
        self._persist_events(chapter, analysis_result)
        self._persist_character_mentions(chapter, analysis_result)
        self._persist_emotion_arcs(chapter, analysis_result)
        self._persist_world_deltas(chapter, analysis_result)

        # 2. Run LLM-based memory merge
        existing_memory = self._collect_existing_memory(chapter.novel_id)
        chapter_facts = self._format_chapter_facts(chapter, analysis_result)

        merge_result = self._run_memory_merge(
            existing_memory=existing_memory,
            chapter_facts=chapter_facts,
            provider_name=provider_name,
            model_name=model_name,
        )

        # 3. Apply merge results
        if merge_result:
            result.new_characters = merge_result.get('new_characters', [])
            result.updated_characters = merge_result.get('updated_characters', [])

            self._apply_new_characters(chapter, result.new_characters)
            self._apply_character_updates(chapter, result.updated_characters)
            self._apply_new_facts(chapter, merge_result.get('new_facts', []))
            self._apply_timeline_events(chapter, merge_result.get('timeline_events', []))
            self._apply_conflicts(chapter, merge_result.get('potential_conflicts', []))

        self.db.commit()
        return result

    # ------------------------------------------------------------------
    # Consistency Checking
    # ------------------------------------------------------------------

    def check_consistency(
        self,
        novel_id: int,
        chapter_id: int,
        provider_name: str,
        model_name: str,
    ) -> list[ConsistencyIssue]:
        """Run consistency check for a chapter against long-term memory."""
        existing_memory = self._collect_existing_memory(novel_id)

        # Get chapter analysis
        analysis = (
            self.db.query(ChapterAnalysis)
            .filter(ChapterAnalysis.chapter_id == chapter_id)
            .one_or_none()
        )

        chapter_facts = ''
        if analysis and analysis.structured_json:
            try:
                parsed = json.loads(analysis.structured_json)
                chapter_facts = json.dumps(parsed, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                chapter_facts = analysis.summary or ''

        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='consistency_check/consistency_check_v1.txt',
            context_block=f'--- 已有记忆 ---\n{existing_memory}\n\n--- 本章事实 ---\n{chapter_facts}',
            output_schema=CONSISTENCY_CHECK_SCHEMA,
        )

        response = self.gateway.call(
            LLMRequest(
                system_prompt=prompt['system'],
                user_prompt=prompt['user'],
                provider_name=provider_name,
                model_name=model_name,
                temperature=0.2,
                max_tokens=2048,
            )
        )

        check_result = parse_and_repair_json(
            response.content, CONSISTENCY_CHECK_SCHEMA
        )

        issues: list[ConsistencyIssue] = []
        for issue_data in check_result.get('issues', []):
            issue = ConsistencyIssue(
                novel_id=novel_id,
                chapter_id=chapter_id,
                issue_type=issue_data.get('issue_type', 'other'),
                severity=issue_data.get('severity', 'medium'),
                description=issue_data.get('description', ''),
                conflicting_claims_json=json.dumps(
                    issue_data.get('conflicting_claims', []), ensure_ascii=False
                ),
                resolution_status='open',
            )
            self.db.add(issue)
            issues.append(issue)

        self.db.commit()
        return issues

    # ------------------------------------------------------------------
    # Internal: Detail persistence (non-LLM)
    # ------------------------------------------------------------------

    def _persist_events(self, chapter: Chapter, analysis_result: dict) -> None:
        for i, event in enumerate(analysis_result.get('key_events', [])):
            ce = ChapterEvent(
                chapter_id=chapter.id,
                novel_id=chapter.novel_id,
                event_index=i,
                event_description=event.get('event', ''),
                evidence_excerpt=event.get('evidence', ''),
                participants_json=json.dumps(
                    event.get('participants', []), ensure_ascii=False
                ),
                event_type=event.get('event_type', 'plot'),
            )
            self.db.add(ce)

    def _persist_character_mentions(self, chapter: Chapter, analysis_result: dict) -> None:
        for char in analysis_result.get('characters', []):
            # Try to match to existing character
            matched = self._match_character_name(
                char.get('name', ''),
                self.db.query(Character)
                .filter(Character.novel_id == chapter.novel_id)
                .all(),
            )

            mention = ChapterCharacterMention(
                chapter_id=chapter.id,
                novel_id=chapter.novel_id,
                character_name=char.get('name', ''),
                character_id=matched.id if matched else None,
                role_in_chapter=char.get('role_in_chapter', ''),
                emotional_state=char.get('emotional_state', ''),
                key_actions=json.dumps(
                    char.get('key_actions', []), ensure_ascii=False
                ),
                relationship_changes=json.dumps(
                    char.get('relationship_changes', []), ensure_ascii=False
                ),
                physical_state=char.get('physical_state', ''),
                power_level_change=char.get('power_level_change', ''),
                location=char.get('location', ''),
            )
            self.db.add(mention)

    def _persist_emotion_arcs(self, chapter: Chapter, analysis_result: dict) -> None:
        for i, arc in enumerate(analysis_result.get('emotion_arcs', [])):
            cea = ChapterEmotionArc(
                chapter_id=chapter.id,
                novel_id=chapter.novel_id,
                segment_index=i,
                segment_label=arc.get('segment_label', ''),
                dominant_emotion=arc.get('dominant_emotion', ''),
                intensity=arc.get('intensity', None),
                description=arc.get('description', ''),
            )
            self.db.add(cea)

    def _persist_world_deltas(self, chapter: Chapter, analysis_result: dict) -> None:
        for delta in analysis_result.get('world_deltas', []):
            cwd = ChapterWorldDelta(
                chapter_id=chapter.id,
                novel_id=chapter.novel_id,
                category=delta.get('category', 'other'),
                name=delta.get('name', ''),
                description=delta.get('description', ''),
                is_new=delta.get('is_new', True),
                evidence=delta.get('evidence', ''),
            )
            self.db.add(cwd)

    # ------------------------------------------------------------------
    # Internal: LLM memory merge
    # ------------------------------------------------------------------

    @llm_retry(max_attempts=3)
    def _run_memory_merge(
        self,
        existing_memory: str,
        chapter_facts: str,
        provider_name: str,
        model_name: str,
    ) -> dict:
        """Call LLM to merge new facts into existing memory."""
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='memory_update/memory_update_v1.txt',
            context_block=f'--- 已有记忆 ---\n{existing_memory}\n\n--- 本章事实 ---\n{chapter_facts}',
            output_schema=MEMORY_UPDATE_SCHEMA,
        )

        response = self.gateway.call(
            LLMRequest(
                system_prompt=prompt['system'],
                user_prompt=prompt['user'],
                provider_name=provider_name,
                model_name=model_name,
                temperature=0.2,
                max_tokens=4096,
                response_format='json_object',
            )
        )

        return parse_and_repair_json(response.content, MEMORY_UPDATE_SCHEMA)

    # ------------------------------------------------------------------
    # Internal: Apply merge results
    # ------------------------------------------------------------------

    def _apply_new_characters(self, chapter: Chapter, new_chars: list[dict]) -> None:
        for char_data in new_chars:
            name = char_data.get('name', '')
            if not name:
                continue

            existing = self._match_character_name(
                name,
                self.db.query(Character)
                .filter(Character.novel_id == chapter.novel_id)
                .all(),
            )
            if existing:
                continue

            # Match faction
            faction_name = char_data.get('faction_affiliation', '')
            faction_id = None
            if faction_name:
                faction = (
                    self.db.query(Faction)
                    .filter(
                        Faction.novel_id == chapter.novel_id,
                        Faction.name == faction_name,
                    )
                    .first()
                )
                if faction:
                    faction_id = faction.id

            character = Character(
                novel_id=chapter.novel_id,
                name=name,
                aliases_json=json.dumps(
                    char_data.get('aliases', []), ensure_ascii=False
                ),
                role=char_data.get('role', 'minor'),
                faction_id=faction_id,
                first_appearance_chapter_id=chapter.id,
                status='alive',
                summary=char_data.get('summary', ''),
                detail_json=json.dumps(
                    {
                        'personality': char_data.get('personality', ''),
                        'appearance': char_data.get('appearance', ''),
                    },
                    ensure_ascii=False,
                ),
            )
            self.db.add(character)
            self.db.flush()

            # Create initial state
            state = CharacterState(
                character_id=character.id,
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                location='',
            )
            self.db.add(state)

            # Create memory claim
            claim = MemoryClaim(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                claim_type='character_fact',
                claim_text=f'新角色 {name} 首次出场',
                target_table='characters',
                target_id=character.id,
                confidence=0.9,
                source_excerpt=char_data.get('first_appearance_evidence', ''),
            )
            self.db.add(claim)

    def _apply_character_updates(
        self, chapter: Chapter, updates: list[dict]
    ) -> None:
        for update_data in updates:
            name = update_data.get('name', '')
            if not name:
                continue

            character = self._match_character_name(
                name,
                self.db.query(Character)
                .filter(Character.novel_id == chapter.novel_id)
                .all(),
            )
            if not character:
                continue

            # Update character summary
            if update_data.get('summary_update'):
                character.summary = update_data['summary_update']

            # Update status if changed
            if update_data.get('status_update') and update_data['status_update'] != character.status:
                character.status = update_data['status_update']

            # Add aliases
            if update_data.get('new_aliases'):
                existing_aliases = json.loads(character.aliases_json or '[]')
                for alias in update_data['new_aliases']:
                    if alias not in existing_aliases:
                        existing_aliases.append(alias)
                character.aliases_json = json.dumps(existing_aliases, ensure_ascii=False)

            # Create new state record
            state = CharacterState(
                character_id=character.id,
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                emotional_state=update_data.get('emotional_state_update', ''),
                physical_state=update_data.get('physical_state_update', ''),
                power_level=update_data.get('power_level_update', ''),
                location=update_data.get('new_location', ''),
            )
            self.db.add(state)

            self.db.flush()

    def _apply_new_facts(self, chapter: Chapter, facts: list[dict]) -> None:
        for fact_data in facts:
            claim_text = fact_data.get('claim_text', '')
            if not claim_text:
                continue

            claim = MemoryClaim(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                claim_type=fact_data.get('claim_type', 'character_fact'),
                claim_text=claim_text,
                target_table='',
                confidence=fact_data.get('confidence', 0.5),
                source_excerpt=fact_data.get('source_excerpt', ''),
            )
            self.db.add(claim)

    def _apply_timeline_events(
        self, chapter: Chapter, events: list[dict]
    ) -> None:
        max_order = (
            self.db.query(TimelineEvent.event_order)
            .filter(TimelineEvent.novel_id == chapter.novel_id)
            .order_by(TimelineEvent.event_order.desc())
            .first()
        )
        base_order = (max_order[0] if max_order else 0) + 1.0

        for i, event_data in enumerate(events):
            event = TimelineEvent(
                novel_id=chapter.novel_id,
                event_name=event_data.get('event_name', ''),
                description=event_data.get('description', ''),
                chapter_id=chapter.id,
                event_order=base_order + i,
                event_type=event_data.get('event_type', 'major_plot'),
                participants_json=json.dumps(
                    event_data.get('participants', []), ensure_ascii=False
                ),
            )
            self.db.add(event)

    def _apply_conflicts(
        self, chapter: Chapter, conflicts: list[dict]
    ) -> None:
        for conflict_data in conflicts:
            issue = ConsistencyIssue(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                issue_type=conflict_data.get(
                    'issue_type', 'setting_conflict'
                ),
                severity=conflict_data.get('severity', 'medium'),
                description=conflict_data.get('description', ''),
                resolution_status='open',
            )
            self.db.add(issue)

    # ------------------------------------------------------------------
    # Internal: Helpers
    # ------------------------------------------------------------------

    def _collect_existing_memory(self, novel_id: int) -> str:
        """Collect all existing long-term memory into a formatted string."""
        parts: list[str] = []

        characters = self.get_characters(novel_id)
        if characters:
            parts.append('=== 角色档案 ===')
            for c in characters:
                parts.append(
                    f'{c.name}（{c.role or ""}）: {c.summary or ""} '
                    f'状态={c.status or ""}'
                )

        factions = self.get_factions(novel_id)
        if factions:
            parts.append('\n=== 势力 ===')
            for f in factions:
                parts.append(f'{f.name}（{f.type or ""}）: {f.description or ""}')

        settings_list = self.get_world_settings(novel_id)
        if settings_list:
            parts.append('\n=== 世界观设定 ===')
            for s in settings_list:
                parts.append(f'[{s.category}] {s.name}: {s.description[:200]}')

        realms = self.get_realm_systems(novel_id)
        if realms:
            parts.append('\n=== 境界体系 ===')
            for r in realms:
                parts.append(f'{r.system_name}: {r.description or ""}')

        timeline = self.get_timeline(novel_id)
        if timeline:
            parts.append('\n=== 时间线 ===')
            for t in timeline:
                parts.append(
                    f'[第{t.chapter_id}章] {t.event_name}: {t.description[:150]}'
                )

        return '\n'.join(parts) if parts else '暂无已有记忆。'

    def _format_chapter_facts(
        self, chapter: Chapter, analysis_result: dict
    ) -> str:
        """Format chapter analysis into a string for the memory merge prompt."""
        return json.dumps(analysis_result, ensure_ascii=False, indent=2)

    @staticmethod
    def _match_character_name(
        name: str, existing_characters: list[Character]
    ) -> Character | None:
        """Match a character name against the character table, including aliases."""
        if not name:
            return None
        for char in existing_characters:
            if char.name == name:
                return char
            if char.aliases_json:
                try:
                    aliases = json.loads(char.aliases_json)
                    if name in aliases:
                        return char
                except json.JSONDecodeError:
                    pass
        return None
