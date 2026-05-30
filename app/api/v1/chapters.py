from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db.models import Chapter, ChapterAnalysis, Novel
from app.infra.db.session import get_db
from app.infra.queue.executor import get_task_queue
from app.schemas.analysis import (
    AnalyzeChapterRequest,
    BatchAnalyzeRequest,
    ChapterAnalysisResponse,
)
from app.schemas.chapter import ChapterResponse
from app.schemas.task import TaskResponse
from app.services.chapter_analysis import ChapterAnalysisService

router = APIRouter()


@router.get('/chapters/{chapter_id}', response_model=ChapterResponse)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> ChapterResponse:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail='章节不存在')
    return chapter


@router.get('/chapters/{chapter_id}/content')
def get_chapter_content(chapter_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail='章节不存在')
    path = chapter.clean_text_path or chapter.raw_text_path
    content = Path(path).read_text(encoding='utf-8') if path else ''
    return {'content': content}


@router.get('/chapters/{chapter_id}/analysis', response_model=ChapterAnalysisResponse | None)
def get_chapter_analysis(chapter_id: int, db: Session = Depends(get_db)) -> ChapterAnalysisResponse | None:
    return db.query(ChapterAnalysis).filter(ChapterAnalysis.chapter_id == chapter_id).one_or_none()


@router.post('/chapters/{chapter_id}/analyze', response_model=ChapterAnalysisResponse)
def analyze_chapter(
    chapter_id: int,
    payload: AnalyzeChapterRequest,
    db: Session = Depends(get_db),
) -> ChapterAnalysisResponse:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail='章节不存在')
    return ChapterAnalysisService(db).analyze(
        chapter=chapter,
        provider_name=payload.provider_name,
        model_name=payload.model_name,
        force_reanalyze=payload.force_reanalyze,
    )


@router.post('/novels/{novel_id}/analyze-batch', response_model=TaskResponse)
def analyze_batch(
    novel_id: int,
    payload: BatchAnalyzeRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Submit a batch analysis task for multiple chapters."""
    novel = db.get(Novel, novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='小说项目不存在')

    # Validate chapter IDs
    chapters = (
        db.query(Chapter)
        .filter(Chapter.id.in_(payload.chapter_ids), Chapter.novel_id == novel_id)
        .all()
    )
    if len(chapters) != len(payload.chapter_ids):
        raise HTTPException(status_code=400, detail='部分章节不存在或不属于该小说')

    from app.domain.entities import WorkflowOptions
    from app.infra.db.models.task import Task
    from app.workflows.batch_analysis_workflow import BatchAnalysisWorkflow

    # Create task record
    task = Task(
        novel_id=novel_id,
        task_type='batch_analysis',
        status='pending',
        provider_name=payload.provider_name,
        model_name=payload.model_name,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Submit to background queue
    options = WorkflowOptions(
        include_revision=payload.include_revision,
        update_memory=payload.update_memory,
        check_consistency=payload.check_consistency,
    )

    get_task_queue().submit(
        task_record=task,
        fn=_run_batch_analysis,
        novel_id=novel_id,
        chapter_ids=payload.chapter_ids,
        provider_name=payload.provider_name,
        model_name=payload.model_name,
        options=options,
    )

    return task


def _run_batch_analysis(
    novel_id: int,
    chapter_ids: list[int],
    provider_name: str,
    model_name: str,
    options: 'WorkflowOptions',
) -> None:
    """Background function for batch analysis."""
    from app.workflows.batch_analysis_workflow import BatchAnalysisWorkflow

    workflow = BatchAnalysisWorkflow()
    workflow.execute(
        novel_id=novel_id,
        chapter_ids=chapter_ids,
        provider_name=provider_name,
        model_name=model_name,
        options=options,
    )
