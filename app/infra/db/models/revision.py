from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class RevisionSuggestion(TimestampMixin, Base):
    __tablename__ = 'revision_suggestions'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    category: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(30), default='medium')
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)
