from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    novel_id: int | None
    chapter_id: int | None
    task_type: str
    status: str
    provider_name: str | None
    model_name: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
