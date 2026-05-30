from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

class Character(TimestampMixin, Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    aliases_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    faction_id: Mapped[int | None] = mapped_column(ForeignKey('factions.id'), nullable=True)
    first_appearance_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    states = relationship('CharacterState', back_populates='character', cascade='all, delete-orphan')


class CharacterState(TimestampMixin, Base):
    __tablename__ = 'character_states'

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    emotional_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    power_level: Mapped[str | None] = mapped_column(String(200), nullable=True)
    faction_affiliation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    relationship_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)

    character = relationship('Character', back_populates='states')


class CharacterRelation(TimestampMixin, Base):
    __tablename__ = 'character_relations'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    character_a_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), index=True)
    character_b_id: Mapped[int] = mapped_column(ForeignKey('characters.id'), index=True)
    relation_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    since_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    last_updated_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


# ---------------------------------------------------------------------------
# Factions
# ---------------------------------------------------------------------------

class Faction(TimestampMixin, Base):
    __tablename__ = 'factions'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    aliases_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_appearance_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)


class FactionRelation(TimestampMixin, Base):
    __tablename__ = 'faction_relations'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    faction_a_id: Mapped[int] = mapped_column(ForeignKey('factions.id'), index=True)
    faction_b_id: Mapped[int] = mapped_column(ForeignKey('factions.id'), index=True)
    relation_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    since_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)


# ---------------------------------------------------------------------------
# World Settings
# ---------------------------------------------------------------------------

class WorldSetting(TimestampMixin, Base):
    __tablename__ = 'world_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    category: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    source_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class RealmSystem(TimestampMixin, Base):
    __tablename__ = 'realm_systems'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    system_name: Mapped[str] = mapped_column(String(200))
    tiers_json: Mapped[str] = mapped_column(Text)
    source_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id'), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineEvent(TimestampMixin, Base):
    __tablename__ = 'timeline_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    event_name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    event_order: Mapped[float] = mapped_column(Float, default=0.0)
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    participants_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------

class MemoryClaim(TimestampMixin, Base):
    __tablename__ = 'memory_claims'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    claim_type: Mapped[str] = mapped_column(String(50))
    claim_text: Mapped[str] = mapped_column(Text)
    target_table: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[int | None] = mapped_column(nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)


class ConsistencyIssue(TimestampMixin, Base):
    __tablename__ = 'consistency_issues'

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey('novels.id'), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id'), index=True)
    issue_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(30), default='medium')
    description: Mapped[str] = mapped_column(Text)
    conflicting_claims_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(50), default='open')
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)
