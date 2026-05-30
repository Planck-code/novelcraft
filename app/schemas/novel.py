from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateNovelRequest(BaseModel):
    title: str
    author_name: str | None = None
    description: str | None = None


class NovelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_name: str | None
    description: str | None
    total_chapters: int
    status: str
    created_at: datetime
    updated_at: datetime
