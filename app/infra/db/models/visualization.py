from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class VisualizationCache(TimestampMixin, Base):
    __tablename__ = 'visualization_cache'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    cache_type: Mapped[str] = mapped_column(String(100))
    cache_key: Mapped[str] = mapped_column(String(200))
    data_json: Mapped[str] = mapped_column(Text)
    data_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
