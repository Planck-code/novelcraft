from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.common.json_repair import parse_and_repair_json, JSONRepairError
from app.common.prompt_builder import build_context_block, build_full_prompt
from app.common.schemas import CHAPTER_ANALYSIS_SCHEMA, CHARACTER_EXTRACT_SCHEMA, WORLDBUILDING_EXTRACT_SCHEMA
from app.common.retry import llm_retry
from app.config.settings import settings
from app.infra.db.models import Chapter, ChapterAnalysis, Task
from app.infra.storage import get_storage
from app.llm.gateway import LLMGateway, LLMRequest

logger = logging.getLogger(__name__)


class ChapterAnalysisService:
    """Service for analyzing a single chapter using LLM.

    Replaces the previous stub implementation with real multi-step LLM calls.
    The minimum agent set runs in order:
    1. Chapter Summary Agent
    2. Character State Agent
    3. Worldbuilding Agent
    4. Aggregate results
    Revision advice and memory update are handled by separate services.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = LLMGateway()
        self.storage = get_storage()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        chapter: Chapter,
        provider_name: str = '',
        model_name: str = '',
        force_reanalyze: bool = False,
    ) -> ChapterAnalysis:
        """Run the full chapter analysis pipeline.

        Returns the persisted ChapterAnalysis record.
        """
        # Resolve defaults
        if not provider_name:
            provider_name = settings.llm_default_provider
        if not model_name:
            model_name = settings.llm_default_model

        # Check for existing analysis
        existing = (
            self.db.query(ChapterAnalysis)
            .filter(ChapterAnalysis.chapter_id == chapter.id)
            .one_or_none()
        )
        if existing and not force_reanalyze:
            return existing

        # Create task record
        task = Task(
            novel_id=chapter.novel_id,
            chapter_id=chapter.id,
            task_type='chapter_analysis',
            status='running',
            provider_name=provider_name,
            model_name=model_name,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # Load chapter text
        path = chapter.clean_text_path or chapter.raw_text_path
        if not path or not Path(path).exists():
            task.status = 'failed'
            task.error_message = 'Chapter text file not found'
            self.db.commit()
            raise FileNotFoundError(f'Chapter text not found: {path}')

        text = Path(path).read_text(encoding='utf-8')

        try:
            # Step 1: Chapter Summary
            summary_result = self._run_chapter_summary(
                text, provider_name, model_name, chapter.title
            )

            # Step 2: Character Extraction
            character_result = self._run_character_extraction(
                text, provider_name, model_name
            )

            # Step 3: Worldbuilding Extraction
            worldbuilding_result = self._run_worldbuilding_extraction(
                text, provider_name, model_name
            )

            # Step 4: Aggregate into a unified structured result
            aggregated = self._aggregate_results(
                summary_result, character_result, worldbuilding_result, text
            )

            # Persist the analysis
            analysis = self._persist_analysis(
                chapter=chapter,
                task=task,
                summary_result=summary_result,
                aggregated=aggregated,
                provider_name=provider_name,
                model_name=model_name,
            )

            chapter.analysis_status = 'success'
            task.status = 'success'
            task.result_json = json.dumps(aggregated, ensure_ascii=False)
            self.db.commit()
            self.db.refresh(analysis)

            return analysis

        except Exception as exc:
            logger.error('Chapter analysis failed for chapter %d: %s', chapter.id, exc)
            task.status = 'failed'
            task.error_message = str(exc)[:2000]
            chapter.analysis_status = 'failed'
            self.db.commit()
            raise

    # ------------------------------------------------------------------
    # Agent Steps
    # ------------------------------------------------------------------

    def _run_chapter_summary(
        self, text: str, provider_name: str, model_name: str, chapter_title: str
    ) -> dict:
        """Step 1: Chapter Summary Agent."""
        context_block = build_context_block(chapter_text=text)
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/chapter_analysis_v1.txt',
            context_block=context_block,
            output_schema=CHAPTER_ANALYSIS_SCHEMA,
            task_variables={'chapter_title': chapter_title},
        )
        response = self._call_llm(prompt, provider_name, model_name)
        return parse_and_repair_json(response.content, CHAPTER_ANALYSIS_SCHEMA)

    def _run_character_extraction(
        self, text: str, provider_name: str, model_name: str
    ) -> dict:
        """Step 2: Character State Agent."""
        context_block = build_context_block(chapter_text=text)
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/character_extract_v1.txt',
            context_block=context_block,
            output_schema=CHARACTER_EXTRACT_SCHEMA,
        )
        response = self._call_llm(prompt, provider_name, model_name)
        return parse_and_repair_json(response.content, CHARACTER_EXTRACT_SCHEMA)

    def _run_worldbuilding_extraction(
        self, text: str, provider_name: str, model_name: str
    ) -> dict:
        """Step 3: Worldbuilding Agent."""
        context_block = build_context_block(chapter_text=text)
        prompt = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/worldbuilding_extract_v1.txt',
            context_block=context_block,
            output_schema=WORLDBUILDING_EXTRACT_SCHEMA,
        )
        response = self._call_llm(prompt, provider_name, model_name)
        return parse_and_repair_json(response.content, WORLDBUILDING_EXTRACT_SCHEMA)

    # ------------------------------------------------------------------
    # Aggregation & Persistence
    # ------------------------------------------------------------------

    def _aggregate_results(
        self,
        summary: dict,
        characters: dict,
        worldbuilding: dict,
        chapter_text: str,
    ) -> dict:
        """Aggregate the outputs of all agents into a unified structured result."""
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
        chapter: Chapter,
        task: Task,
        summary_result: dict,
        aggregated: dict,
        provider_name: str,
        model_name: str,
    ) -> ChapterAnalysis:
        """Save analysis results to DB."""
        existing = (
            self.db.query(ChapterAnalysis)
            .filter(ChapterAnalysis.chapter_id == chapter.id)
            .one_or_none()
        )

        # Save raw LLM response to file
        raw_response_path = self.storage.write_text(
            f'analysis_results/{chapter.novel_id}/{chapter.id:04d}_raw_response.json',
            json.dumps(aggregated, ensure_ascii=False, indent=2),
        )

        if existing and task.task_type == 'chapter_analysis':
            # Update existing record
            existing.summary = summary_result.get('summary', '')
            existing.emotion_overview = summary_result.get('emotion_overview', '')
            existing.battle_conflict_summary = summary_result.get('conflict_summary', '')
            existing.world_building_delta_summary = summary_result.get(
                'world_building_delta_summary', ''
            )
            existing.foreshadowing_summary = summary_result.get('foreshadowing_summary', '')
            existing.structured_json = json.dumps(aggregated, ensure_ascii=False)
            existing.raw_response_path = str(raw_response_path)
            existing.provider_name = provider_name
            existing.model_name = model_name
            existing.prompt_version = 'v1'
            existing.analysis_version = 'v1'
            existing.parse_status = 'success'
            self.db.flush()
            return existing
        else:
            analysis = ChapterAnalysis(
                novel_id=chapter.novel_id,
                chapter_id=chapter.id,
                summary=summary_result.get('summary', ''),
                emotion_overview=summary_result.get('emotion_overview', ''),
                battle_conflict_summary=summary_result.get('conflict_summary', ''),
                world_building_delta_summary=summary_result.get(
                    'world_building_delta_summary', ''
                ),
                foreshadowing_summary=summary_result.get('foreshadowing_summary', ''),
                structured_json=json.dumps(aggregated, ensure_ascii=False),
                raw_response_path=str(raw_response_path),
                analysis_version='v1',
                prompt_version='v1',
                provider_name=provider_name,
                model_name=model_name,
                parse_status='success',
            )
            self.db.add(analysis)
            self.db.flush()
            return analysis

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @llm_retry(max_attempts=3)
    def _call_llm(
        self, prompt: dict, provider_name: str, model_name: str
    ) -> object:
        """Call the LLM gateway with retry logic.

        The return type is object because the tenacity decorator
        doesn't preserve the type annotation through retry wrapping.
        """
        from app.llm.gateway import LLMResponse

        request = LLMRequest(
            system_prompt=prompt['system'],
            user_prompt=prompt['user'],
            provider_name=provider_name,
            model_name=model_name,
            temperature=0.3,
            max_tokens=4096,
            response_format='json_object',
        )
        response: LLMResponse = self.gateway.call(request)
        return response
