from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base, TimestampMixin


class Task(TimestampMixin, Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int | None] = mapped_column(ForeignKey('novels.id'), nullable=True, index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(index=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    provider_name: Mapped[str | None] = mapped_column(nullable=True)
    model_name: Mapped[str | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    novel = relationship('Novel', back_populates='tasks')
    chapter = relationship('Chapter', back_populates='tasks')
