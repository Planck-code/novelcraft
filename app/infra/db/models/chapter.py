from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base, TimestampMixin


class Chapter(TimestampMixin, Base):
    __tablename__ = 'chapters'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_no: Mapped[int] = mapped_column(Integer)
    volume_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    raw_text_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    clean_text_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_status: Mapped[str] = mapped_column(String(50), default='pending')
    analysis_status: Mapped[str] = mapped_column(String(50), default='pending')

    novel = relationship('Novel', back_populates='chapters')
    analysis = relationship('ChapterAnalysis', back_populates='chapter', uselist=False, cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='chapter', cascade='all, delete-orphan')
