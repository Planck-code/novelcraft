from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base, TimestampMixin


class Novel(TimestampMixin, Base):
    __tablename__ = 'novels'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_chapters: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(50), default='draft')

    chapters = relationship('Chapter', back_populates='novel', cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='novel', cascade='all, delete-orphan')
