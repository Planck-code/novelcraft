from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.domain.entities import WorkflowOptions
from app.infra.db.models.chapter import Chapter
from app.infra.db.models.task import Task
from app.infra.db.session import SessionLocal
from app.workflows.chapter_analysis_workflow import ChapterAnalysisWorkflow, WorkflowState

logger = logging.getLogger(__name__)


class BatchAnalysisWorkflow:
    """Orchestrates analysis for multiple chapters sequentially.

    For MVP, chapters are processed one at a time to avoid
    API rate limit exhaustion.
    """

    def execute(
        self,
        novel_id: int,
        chapter_ids: list[int],
        provider_name: str,
        model_name: str,
        options: WorkflowOptions | None = None,
    ) -> list[WorkflowState]:
        """Execute analysis for a list of chapter IDs sequentially."""
        if options is None:
            options = WorkflowOptions()

        db: Session = SessionLocal()
        results: list[WorkflowState] = []

        # Create a batch task
        batch_task = Task(
            novel_id=novel_id,
            task_type='batch_analysis',
            status='running',
            provider_name=provider_name,
            model_name=model_name,
            payload_json=json.dumps(
                {'chapter_ids': chapter_ids, 'total': len(chapter_ids)},
                ensure_ascii=False,
            ),
        )
        db.add(batch_task)
        db.commit()
        db.refresh(batch_task)
        db.close()

        workflow = ChapterAnalysisWorkflow()
        completed = 0
        failed = 0

        for chapter_id in chapter_ids:
            db = SessionLocal()
            try:
                chapter = db.get(Chapter, chapter_id)
                if not chapter:
                    logger.warning('Chapter %d not found, skipping', chapter_id)
                    continue

                logger.info(
                    'Batch: analyzing chapter %d/%d (id=%d)',
                    completed + failed + 1,
                    len(chapter_ids),
                    chapter_id,
                )

                state = workflow.execute(
                    chapter=chapter,
                    provider_name=provider_name,
                    model_name=model_name,
                    options=options,
                )
                results.append(state)

                if state.status == 'success':
                    completed += 1
                else:
                    failed += 1

                # Update batch task progress
                batch = db.get(Task, batch_task.id)
                if batch:
                    batch.result_json = json.dumps(
                        {
                            'completed': completed,
                            'failed': failed,
                            'total': len(chapter_ids),
                            'current_chapter_id': chapter_id,
                        },
                        ensure_ascii=False,
                    )
                    db.commit()

            except Exception as e:
                logger.error('Batch chapter %d failed: %s', chapter_id, e)
                failed += 1
            finally:
                db.close()

        # Finalize batch task
        db = SessionLocal()
        try:
            batch = db.get(Task, batch_task.id)
            if batch:
                batch.status = 'success' if failed == 0 else 'partial_success'
                batch.result_json = json.dumps(
                    {
                        'completed': completed,
                        'failed': failed,
                        'total': len(chapter_ids),
                    },
                    ensure_ascii=False,
                )
                db.commit()
        finally:
            db.close()

        logger.info('Batch analysis complete: %d completed, %d failed', completed, failed)
        return results
