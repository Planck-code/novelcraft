from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.config.settings import settings
from app.infra.db.models import Chapter, ChapterAnalysis
from app.infra.db.session import get_db, init_db


app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / 'web' / 'templates'))
app.mount('/static', StaticFiles(directory=str(Path(__file__).resolve().parent / 'web' / 'static')), name='static')
app.include_router(api_router)


@app.on_event('startup')
def startup_event() -> None:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.novels_dir.mkdir(parents=True, exist_ok=True)
    settings.analysis_results_dir.mkdir(parents=True, exist_ok=True)
    init_db()


# --- Page Routes ---


@app.get('/', response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    from app.modules.project_management.service import ProjectManagementService

    novels = ProjectManagementService(db).list_novels()
    return templates.TemplateResponse(
        'index.html', {'request': request, 'novels': novels, 'app_name': settings.app_name}
    )


@app.get('/novels/{novel_id}', response_class=HTMLResponse)
def novel_detail(novel_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    from app.modules.project_management.service import ProjectManagementService

    novel = ProjectManagementService(db).get_novel(novel_id)
    chapters = []
    if novel:
        chapters = (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_no.asc())
            .all()
        )
    return templates.TemplateResponse(
        'novel_detail.html', {'request': request, 'novel': novel, 'chapters': chapters}
    )


@app.get('/chapters/{chapter_id}/view', response_class=HTMLResponse)
def chapter_detail(chapter_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    chapter = db.get(Chapter, chapter_id)
    analysis = (
        db.query(ChapterAnalysis)
        .filter(ChapterAnalysis.chapter_id == chapter_id)
        .one_or_none()
    )
    content = ''
    if chapter and chapter.clean_text_path:
        content = Path(chapter.clean_text_path).read_text(encoding='utf-8')
    return templates.TemplateResponse(
        'chapter_detail.html',
        {'request': request, 'chapter': chapter, 'analysis': analysis, 'content': content},
    )


@app.get('/novels/{novel_id}/memory', response_class=HTMLResponse)
def memory_center(novel_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    from app.modules.project_management.service import ProjectManagementService
    from app.modules.memory_center.service import MemoryCenterService

    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        return templates.TemplateResponse('index.html', {'request': request, 'novels': [], 'app_name': settings.app_name})

    memory_service = MemoryCenterService(db)
    characters = memory_service.get_characters(novel_id)
    factions = memory_service.get_factions(novel_id)
    timeline = memory_service.get_timeline(novel_id)
    issues = memory_service.get_consistency_issues(novel_id)

    return templates.TemplateResponse(
        'memory_center.html',
        {
            'request': request,
            'novel': novel,
            'characters': characters,
            'factions': factions,
            'timeline': timeline,
            'issues': issues,
        },
    )
