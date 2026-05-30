from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db.models import Task
from app.infra.db.session import get_db
from app.schemas.task import TaskResponse


router = APIRouter()


@router.get('', response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskResponse]:
    return db.query(Task).order_by(Task.created_at.desc()).all()


@router.get('/{task_id}', response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='?????')
    return task
