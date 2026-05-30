from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base, TimestampMixin


class ChapterAnalysis(TimestampMixin, Base):
    __tablename__ = 'chapter_analyses'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text)
    emotion_overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    battle_conflict_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    world_building_delta_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    foreshadowing_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response_path: Mapped[str | None] = mapped_column(nullable=True)
    analysis_version: Mapped[str] = mapped_column(default='bootstrap-v1')
    prompt_version: Mapped[str] = mapped_column(default='bootstrap-v1')
    provider_name: Mapped[str] = mapped_column(default='stub')
    model_name: Mapped[str] = mapped_column(default='stub')
    parse_status: Mapped[str] = mapped_column(default='success')

    chapter = relationship('Chapter', back_populates='analysis')
