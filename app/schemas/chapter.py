from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    novel_id: int
    chapter_no: int
    title: str
    word_count: int
    parse_status: str
    analysis_status: str
    created_at: datetime
