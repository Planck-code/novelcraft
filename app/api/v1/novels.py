from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.infra.db.models import Chapter
from app.infra.db.session import get_db
from app.modules.novel_import.service import NovelImportService
from app.modules.project_management.service import ProjectManagementService
from app.schemas.chapter import ChapterResponse
from app.schemas.novel import CreateNovelRequest, NovelResponse
from app.schemas.task import TaskResponse


router = APIRouter()


@router.get('', response_model=list[NovelResponse])
def list_novels(db: Session = Depends(get_db)) -> list[NovelResponse]:
    return ProjectManagementService(db).list_novels()


@router.post('', response_model=NovelResponse)
def create_novel(payload: CreateNovelRequest, db: Session = Depends(get_db)) -> NovelResponse:
    return ProjectManagementService(db).create_novel(payload)


@router.get('/{novel_id}', response_model=NovelResponse)
def get_novel(novel_id: int, db: Session = Depends(get_db)) -> NovelResponse:
    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='???????')
    return novel


@router.get('/{novel_id}/chapters', response_model=list[ChapterResponse])
def list_chapters(novel_id: int, db: Session = Depends(get_db)) -> list[ChapterResponse]:
    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='???????')
    return db.query(Chapter).filter(Chapter.novel_id == novel_id).order_by(Chapter.chapter_no.asc()).all()


@router.post('/{novel_id}/import-txt', response_model=TaskResponse)
async def import_txt(novel_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)) -> TaskResponse:
    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='???????')
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail='??????')
    return NovelImportService(db).import_txt(novel=novel, filename=file.filename or 'novel.txt', content=content)
