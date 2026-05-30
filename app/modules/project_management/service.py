from __future__ import annotations

from sqlalchemy.orm import Session

from app.infra.db.models import Novel
from app.schemas.novel import CreateNovelRequest


class ProjectManagementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_novel(self, payload: CreateNovelRequest) -> Novel:
        novel = Novel(
            title=payload.title.strip(),
            author_name=payload.author_name,
            description=payload.description,
            status='draft',
        )
        self.db.add(novel)
        self.db.commit()
        self.db.refresh(novel)
        return novel

    def list_novels(self) -> list[Novel]:
        return self.db.query(Novel).order_by(Novel.updated_at.desc()).all()

    def get_novel(self, novel_id: int) -> Novel | None:
        return self.db.get(Novel, novel_id)
