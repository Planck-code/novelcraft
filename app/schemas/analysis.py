from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalyzeChapterRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider_name: str = ''
    model_name: str = ''
    force_reanalyze: bool = False


class BatchAnalyzeRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    chapter_ids: list[int]
    provider_name: str = ''
    model_name: str = ''
    include_revision: bool = True
    update_memory: bool = True
    check_consistency: bool = False


class ChapterAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    chapter_id: int
    summary: str
    emotion_overview: str | None
    battle_conflict_summary: str | None
    world_building_delta_summary: str | None
    foreshadowing_summary: str | None
    provider_name: str
    model_name: str
    created_at: datetime
    updated_at: datetime
