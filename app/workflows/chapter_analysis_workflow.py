from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.common.json_repair import parse_and_repair_json
from app.common.prompt_builder import build_context_block, build_full_prompt
from app.common.schemas import (
    CHAPTER_ANALYSIS_SCHEMA,
    CHARACTER_EXTRACT_SCHEMA,
    WORLDBUILDING_EXTRACT_SCHEMA,
    REVISION_ADVICE_SCHEMA,
    MEMORY_UPDATE_SCHEMA,
    CONSISTENCY_CHECK_SCHEMA,
)
from app.common.retry import llm_retry
from app.domain.entities import WorkflowOptions
from app.infra.db.models.chapter import Chapter
from app.infra.db.models.analysis import ChapterAnalysis
from app.infra.db.models.task import Task
from app.infra.db.session import SessionLocal
from app.infra.storage import get_storage
from app.llm.gateway import LLMGateway, LLMRequest
from app.modules.memory_center.service import MemoryCenterService
from app.modules.revision_advice.service import RevisionAdviceService

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """Tracks the state of a multi-step analysis workflow."""
    task_id: int
    novel_id: int
    chapter_id: int
    provider_name: str
    model_name: str
    current_step: str = ''
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    partial_results: dict = field(default_factory=dict)
    status: str = 'pending'


class ChapterAnalysisWorkflow:
    """Orchestrates the full analysis pipeline for a single chapter.

    Steps (ordered per design doc Section 9.4):
    1. chapter_summary
    2. character_extraction
    3. worldbuilding_extraction
    4. aggregation
    5. revision_advice (optional)
    6. memory_update (optional)
    7. consistency_check (optional)

    Each step can fail independently. Partial results are preserved.
    """

    def __init__(self) -> None:
        self.gateway = LLMGateway()
        self.storage = get_storage()

    def execute(
        self,
        chapter: Chapter,
        provider_name: str,
        model_name: str,
        options: WorkflowOptions | None = None,
    ) -> WorkflowState:
        """Execute the full workflow synchronously."""
        if options is None:
            options = WorkflowOptions()

        db: Session = SessionLocal()
        try:
            # Re-attach chapter to this session
            chapter = db.get(Chapter, chapter.id)
            if not chapter:
                raise ValueError(f'Chapter {chapter.id} not found')

            # Create or reuse task
            task = Task(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                task_type='chapter_analysis_workflow',
                status='running',
                provider_name=provider_name,
                model_name=model_name,
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            state = WorkflowState(
                task_id=task.id,
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                provider_name=provider_name,
                model_name=model_name,
                status='running',
            )

            memory_service = MemoryCenterService(db)
            revision_service = RevisionAdviceService(db)

            # Load chapter text
            path = chapter.clean_text_path or chapter.raw_text_path
            text = Path(path).read_text(encoding='utf-8') if path else ''

            # Check for existing analysis (skip if present and not forced)
            existing = db.query(ChapterAnalysis).filter(
                ChapterAnalysis.chapter_id == chapter.id
            ).one_or_none()

            if existing and not options.force_reanalyze:
                state.status = 'success'
                state.steps_completed = ['cached']
                task.status = 'success'
                db.commit()
                return state

            # Build context
            char_context = memory_service.build_character_context(chapter.novel_id)
            world_context = memory_service.build_world_context(chapter.novel_id)
            recent_context = memory_service.build_recent_context(
                chapter.novel_id, chapter.chapter_no
            )

            context_block = build_context_block(
                chapter_text=text,
                previous_chapter_summaries=[recent_context] if recent_context else None,
            )
            if char_context:
                context_block += f'\n\n{char_context}'
            if world_context:
                context_block += f'\n\n{world_context}'

            # Step 1: Chapter Summary
            state.current_step = 'chapter_summary'
            try:
                summary_result = self._step_chapter_summary(
                    context_block, provider_name, model_name
                )
                state.partial_results['summary'] = summary_result
                state.steps_completed.append('chapter_summary')
            except Exception as e:
                logger.error('chapter_summary failed: %s', e)
                state.steps_failed.append('chapter_summary')

            # Step 2: Character Extraction
            state.current_step = 'character_extraction'
            try:
                char_result = self._step_character_extraction(
                    context_block, provider_name, model_name
                )
                state.partial_results['characters'] = char_result
                state.steps_completed.append('character_extraction')
            except Exception as e:
                logger.error('character_extraction failed: %s', e)
                state.steps_failed.append('character_extraction')

            # Step 3: Worldbuilding Extraction
            state.current_step = 'worldbuilding_extraction'
            try:
                wb_result = self._step_worldbuilding_extraction(
                    context_block, provider_name, model_name
                )
                state.partial_results['worldbuilding'] = wb_result
                state.steps_completed.append('worldbuilding_extraction')
            except Exception as e:
                logger.error('worldbuilding_extraction failed: %s', e)
                state.steps_failed.append('worldbuilding_extraction')

            # Step 4: Aggregate and persist
            state.current_step = 'aggregation'
            try:
                aggregated = self._aggregate(
                    state.partial_results, text
                )
                state.partial_results['aggregated'] = aggregated
                self._persist_analysis(db, chapter, task, aggregated, provider_name, model_name)
                state.steps_completed.append('aggregation')
            except Exception as e:
                logger.error('aggregation failed: %s', e)
                state.steps_failed.append('aggregation')

            # Step 5: Revision Advice (optional)
            if options.include_revision:
                state.current_step = 'revision_advice'
                try:
                    analysis = db.query(ChapterAnalysis).filter(
                        ChapterAnalysis.chapter_id == chapter.id
                    ).one_or_none()
                    revision_service.generate(
                        chapter=chapter,
                        analysis=analysis,
                        provider_name=provider_name,
                        model_name=model_name,
                    )
                    state.steps_completed.append('revision_advice')
                except Exception as e:
                    logger.error('revision_advice failed: %s', e)
                    state.steps_failed.append('revision_advice')

            # Step 6: Memory Update (optional)
            if options.update_memory:
                state.current_step = 'memory_update'
                try:
                    memory_service.update_from_analysis(
                        chapter=chapter,
                        analysis_result=state.partial_results.get('aggregated', {}),
                        provider_name=provider_name,
                        model_name=model_name,
                    )
                    state.steps_completed.append('memory_update')
                except Exception as e:
                    logger.error('memory_update failed: %s', e)
                    state.steps_failed.append('memory_update')

            # Step 7: Consistency Check (optional)
            if options.check_consistency:
                state.current_step = 'consistency_check'
                try:
                    memory_service.check_consistency(
                        novel_id=chapter.novel_id,
                        chapter_id=chapter.id,
                        provider_name=provider_name,
                        model_name=model_name,
                    )
                    state.steps_completed.append('consistency_check')
                except Exception as e:
                    logger.error('consistency_check failed: %s', e)
                    state.steps_failed.append('consistency_check')

            # Finalize
            if state.steps_failed:
                state.status = 'partial_success'
                task.status = 'partial_success'
                task.error_message = f'Failed steps: {", ".join(state.steps_failed)}'
            else:
                state.status = 'success'
                task.status = 'success'
                chapter.analysis_status = 'success'

            task.result_json = json.dumps(
                {
                    'steps_completed': state.steps_completed,
                    'steps_failed': state.steps_failed,
                },
                ensure_ascii=False,
            )
            db.commit()

            return state

        except Exception as e:
            logger.error('Workflow failed: %s', e)
            state = WorkflowState(
                task_id=0,
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                provider_name=provider_name,
                model_name=model_name,
                status='failed',
            )
            return state
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Individual Steps
    # ------------------------------------------------------------------

    @llm_retry(max_attempts=3)
    def _step_chapter_summary(self, context_block: str, provider_name: str, model_name: str) -> dict:
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/chapter_analysis_v1.txt',
            context_block=context_block,
            output_schema=CHAPTER_ANALYSIS_SCHEMA,
        )
        request = LLMRequest(
            system_prompt=prompt['system'],
            user_prompt=prompt['user'],
            provider_name=provider_name,
            model_name=model_name,
            temperature=0.3,
            max_tokens=4096,
            response_format='json_object',
        )
        response = self.gateway.call(request)
        return parse_and_repair_json(response.content, CHAPTER_ANALYSIS_SCHEMA)

    @llm_retry(max_attempts=3)
    def _step_character_extraction(self, context_block: str, provider_name: str, model_name: str) -> dict:
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/character_extract_v1.txt',
            context_block=context_block,
            output_schema=CHARACTER_EXTRACT_SCHEMA,
        )
        request = LLMRequest(
            system_prompt=prompt['system'],
            user_prompt=prompt['user'],
            provider_name=provider_name,
            model_name=model_name,
            temperature=0.3,
            max_tokens=4096,
            response_format='json_object',
        )
        response = self.gateway.call(request)
        return parse_and_repair_json(response.content, CHARACTER_EXTRACT_SCHEMA)

    @llm_retry(max_attempts=3)
    def _step_worldbuilding_extraction(self, context_block: str, provider_name: str, model_name: str) -> dict:
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/worldbuilding_extract_v1.txt',
            context_block=context_block,
            output_schema=WORLDBUILDING_EXTRACT_SCHEMA,
        )
        request = LLMRequest(
            system_prompt=prompt['system'],
            user_prompt=prompt['user'],
            provider_name=provider_name,
            model_name=model_name,
            temperature=0.3,
            max_tokens=4096,
            response_format='json_object',
        )
        response = self.gateway.call(request)
        return parse_and_repair_json(response.content, WORLDBUILDING_EXTRACT_SCHEMA)

    def _aggregate(self, partial_results: dict, chapter_text: str) -> dict:
        summary = partial_results.get('summary', {})
        characters = partial_results.get('characters', {})
        worldbuilding = partial_results.get('worldbuilding', {})

        return {
            'summary': summary.get('summary', ''),
            'key_events': summary.get('key_events', []),
            'emotion_overview': summary.get('emotion_overview', ''),
            'conflict_summary': summary.get('conflict_summary', ''),
            'world_building_delta_summary': summary.get('world_building_delta_summary', ''),
            'foreshadowing_summary': summary.get('foreshadowing_summary', ''),
            'emotion_arcs': summary.get('emotion_arcs', []),
            'overall_quality_notes': summary.get('overall_quality_notes', ''),
            'characters': characters.get('characters', []),
            'world_deltas': worldbuilding.get('world_deltas', []),
            'realm_changes': worldbuilding.get('realm_changes', []),
            'faction_changes': worldbuilding.get('faction_changes', []),
            'chapter_word_count': len(chapter_text),
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
        }

    def _persist_analysis(
        self,
        db: Session,
        chapter: Chapter,
        task: Task,
        aggregated: dict,
        provider_name: str,
        model_name: str,
    ) -> None:
        summary = aggregated.get('summary', '')

        existing = db.query(ChapterAnalysis).filter(
            ChapterAnalysis.chapter_id == chapter.id
        ).one_or_none()

        raw_path = self.storage.write_text(
            f'analysis_results/{chapter.novel_id}/{chapter.id:04d}_raw_response.json',
            json.dumps(aggregated, ensure_ascii=False, indent=2),
        )

        if existing:
            existing.summary = summary
            existing.emotion_overview = aggregated.get('emotion_overview', '')
            existing.battle_conflict_summary = aggregated.get('conflict_summary', '')
            existing.world_building_delta_summary = aggregated.get(
                'world_building_delta_summary', ''
            )
            existing.foreshadowing_summary = aggregated.get('foreshadowing_summary', '')
            existing.structured_json = json.dumps(aggregated, ensure_ascii=False)
            existing.raw_response_path = str(raw_path)
            existing.provider_name = provider_name
            existing.model_name = model_name
            existing.parse_status = 'success'
        else:
            analysis = ChapterAnalysis(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                summary=summary,
                emotion_overview=aggregated.get('emotion_overview', ''),
                battle_conflict_summary=aggregated.get('conflict_summary', ''),
                world_building_delta_summary=aggregated.get(
                    'world_building_delta_summary', ''
                ),
                foreshadowing_summary=aggregated.get('foreshadowing_summary', ''),
                structured_json=json.dumps(aggregated, ensure_ascii=False),
                raw_response_path=str(raw_path),
                analysis_version='v1',
                prompt_version='v1',
                provider_name=provider_name,
                model_name=model_name,
                parse_status='success',
            )
            db.add(analysis)

        chapter.analysis_status = 'success'
