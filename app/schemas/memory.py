from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    role: str | None
    faction_id: int | None
    first_appearance_chapter_id: int | None
    status: str | None
    summary: str | None
    created_at: datetime


class CharacterDetailResponse(CharacterResponse):
    aliases_json: str | None = None
    detail_json: str | None = None


class CharacterStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chapter_id: int
    emotional_state: str | None
    physical_state: str | None
    power_level: str | None
    location: str | None
    created_at: datetime


class CharacterRelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    character_a_id: int
    character_b_id: int
    relation_type: str
    description: str | None


class FactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str | None
    description: str | None
    first_appearance_chapter_id: int | None
    status: str | None


class WorldSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    name: str
    description: str


class RealmSystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    system_name: str
    tiers_json: str
    description: str | None


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_name: str
    description: str
    chapter_id: int
    event_order: float
    event_type: str | None
    created_at: datetime


class ConsistencyIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chapter_id: int
    issue_type: str
    severity: str
    description: str
    resolution_status: str
    created_at: datetime


class RevisionSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chapter_id: int
    category: str
    severity: str
    title: str
    description: str
    suggestion: str
    excerpt: str | None


class GenerateRevisionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider_name: str = ''
    model_name: str = ''
