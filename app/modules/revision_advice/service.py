from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.common.json_repair import parse_and_repair_json
from app.common.prompt_builder import build_context_block, build_full_prompt
from app.common.schemas import REVISION_ADVICE_SCHEMA
from app.common.retry import llm_retry
from app.config.settings import settings
from app.infra.db.models.analysis import ChapterAnalysis
from app.infra.db.models.chapter import Chapter
from app.infra.db.models.revision import RevisionSuggestion
from app.infra.db.models.task import Task
from app.llm.gateway import LLMGateway, LLMRequest
from app.modules.memory_center.service import MemoryCenterService

logger = logging.getLogger(__name__)


class RevisionAdviceService:
    """Generates structured revision advice for a chapter using LLM."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = LLMGateway()
        self.memory_center = MemoryCenterService(db)

    def generate(
        self,
        chapter: Chapter,
        analysis: ChapterAnalysis | None = None,
        provider_name: str = '',
        model_name: str = '',
    ) -> list[RevisionSuggestion]:
        """Generate revision advice for a chapter.

        Returns a list of persisted RevisionSuggestion records.
        """
        if not provider_name:
            provider_name = settings.llm_default_provider
        if not model_name:
            model_name = settings.llm_default_model

        # Create task record
        task = Task(
            novel_id=chapter.novel_id,
            chapter_id=chapter.id,
            task_type='revision_advice',
            status='running',
            provider_name=provider_name,
            model_name=model_name,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        try:
            # Load chapter text
            path = chapter.clean_text_path or chapter.raw_text_path
            text = Path(path).read_text(encoding='utf-8') if path else ''

            # Build context
            # Previous chapter summaries
            prev_summaries = self._get_previous_summaries(chapter)

            # Character context
            char_context = self.memory_center.build_character_context(chapter.novel_id)

            # World context
            world_context = self.memory_center.build_world_context(chapter.novel_id)

            # Chapter analysis summary
            analysis_text = ''
            if analysis:
                analysis_text = f'本章摘要: {analysis.summary}\n'
                analysis_text += f'情绪评估: {analysis.emotion_overview or ""}\n'
                analysis_text += f'冲突总结: {analysis.battle_conflict_summary or ""}\n'

            context_block = build_context_block(
                chapter_text=text,
                previous_chapter_summaries=prev_summaries,
            )
            # Append additional context
            if char_context:
                context_block += f'\n\n--- 角色上下文 ---\n{char_context}'
            if world_context:
                context_block += f'\n\n--- 世界观上下文 ---\n{world_context}'
            if analysis_text:
                context_block += f'\n\n--- 本章分析 ---\n{analysis_text}'

            # Build prompt
            prompt = build_full_prompt(
                system_prompt_name='system/webnovel_analyst_v1.txt',
                task_prompt_name='revision_advice/revision_advice_v1.txt',
                context_block=context_block,
                output_schema=REVISION_ADVICE_SCHEMA,
            )

            # Call LLM
            response = self._call_llm_for_advice(
                prompt, provider_name, model_name
            )

            # Parse response
            result = parse_and_repair_json(
                response.content, REVISION_ADVICE_SCHEMA
            )

            # Delete old suggestions for this chapter
            self.db.query(RevisionSuggestion).filter(
                RevisionSuggestion.chapter_id == chapter.id
            ).delete()

            # Persist new suggestions
            suggestions: list[RevisionSuggestion] = []
            for item in result.get('advice_items', []):
                suggestion = RevisionSuggestion(
                    novel_id=chapter.novel_id,
                    chapter_id=chapter.id,
                    category=item.get('category', 'other'),
                    severity=item.get('severity', 'medium'),
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    suggestion=item.get('suggestion', ''),
                    excerpt=item.get('excerpt', ''),
                    provider_name=provider_name,
                    model_name=model_name,
                    source_task_id=task.id,
                )
                self.db.add(suggestion)
                suggestions.append(suggestion)

            task.status = 'success'
            task.result_json = json.dumps(
                {'advice_count': len(suggestions)}, ensure_ascii=False
            )
            self.db.commit()

            return suggestions

        except Exception as exc:
            logger.error('Revision advice generation failed for chapter %d: %s', chapter.id, exc)
            task.status = 'failed'
            task.error_message = str(exc)[:2000]
            self.db.commit()
            raise

    def get_for_chapter(self, chapter_id: int) -> list[RevisionSuggestion]:
        """Get existing revision suggestions for a chapter."""
        return (
            self.db.query(RevisionSuggestion)
            .filter(RevisionSuggestion.chapter_id == chapter_id)
            .order_by(RevisionSuggestion.severity.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_previous_summaries(self, chapter: Chapter, count: int = 3) -> list[str]:
        """Get summaries of previous chapters."""
        from app.infra.db.models.chapter import Chapter as ChapterModel

        prev_chapters = (
            self.db.query(ChapterModel)
            .filter(
                ChapterModel.novel_id == chapter.novel_id,
                ChapterModel.chapter_no < chapter.chapter_no,
            )
            .order_by(ChapterModel.chapter_no.desc())
            .limit(count)
            .all()
        )

        summaries: list[str] = []
        for ch in reversed(prev_chapters):
            analysis = (
                self.db.query(ChapterAnalysis)
                .filter(ChapterAnalysis.chapter_id == ch.id)
                .one_or_none()
            )
            if analysis:
                summaries.append(
                    f'第{ch.chapter_no}章 {ch.title}: {analysis.summary[:200]}'
                )

        return summaries

    @llm_retry(max_attempts=3)
    def _call_llm_for_advice(
        self, prompt: dict, provider_name: str, model_name: str
    ) -> object:
        """Call LLM with retry for revision advice."""
        request = LLMRequest(
            system_prompt=prompt['system'],
            user_prompt=prompt['user'],
            provider_name=provider_name,
            model_name=model_name,
            temperature=0.4,
            max_tokens=4096,
            response_format='json_object',
        )
        return self.gateway.call(request)
