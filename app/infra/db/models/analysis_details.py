from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class ChapterEvent(TimestampMixin, Base):
    __tablename__ = 'chapter_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    event_index: Mapped[int] = mapped_column(Integer, default=0)
    event_description: Mapped[str] = mapped_column(Text)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    participants_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


class ChapterCharacterMention(TimestampMixin, Base):
    __tablename__ = 'chapter_character_mentions'

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    character_name: Mapped[str] = mapped_column(String(100), index=True)
    character_id: Mapped[int | None] = mapped_column(ForeignKey('characters.id'), nullable=True, index=True)
    role_in_chapter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emotional_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    relationship_changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    power_level_change: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


class ChapterEmotionArc(TimestampMixin, Base):
    __tablename__ = 'chapter_emotion_arcs'

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    segment_index: Mapped[int] = mapped_column(Integer, default=0)
    segment_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dominant_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    intensity: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


class ChapterWorldDelta(TimestampMixin, Base):
    __tablename__ = 'chapter_world_deltas'

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    category: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


class ChapterForeshadowing(TimestampMixin, Base):
    __tablename__ = 'chapter_foreshadowings'

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    description: Mapped[str] = mapped_column(Text)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='planted')
    payoff_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)
