from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.modules.project_management.service import ProjectManagementService
from app.modules.visualization.service import VisualizationService

router = APIRouter()


@router.get('/{novel_id}/character-graph')
def get_character_graph(novel_id: int, db: Session = Depends(get_db)):
    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='小说项目不存在')
    return VisualizationService(db).get_character_graph(novel_id)


@router.get('/{novel_id}/emotion-curve')
def get_emotion_curve(
    novel_id: int,
    character_id: int | None = None,
    db: Session = Depends(get_db),
):
    return VisualizationService(db).get_emotion_curve(novel_id, character_id)


@router.get('/{novel_id}/character-frequency')
def get_character_frequency(novel_id: int, db: Session = Depends(get_db)):
    return VisualizationService(db).get_character_frequency(novel_id)


@router.get('/{novel_id}/faction-evolution')
def get_faction_evolution(novel_id: int, db: Session = Depends(get_db)):
    return VisualizationService(db).get_faction_evolution(novel_id)


@router.get('/{novel_id}/timeline-data')
def get_timeline_data(novel_id: int, db: Session = Depends(get_db)):
    return VisualizationService(db).get_timeline_data(novel_id)


@router.get('/{novel_id}/stats')
def get_novel_stats(novel_id: int, db: Session = Depends(get_db)):
    return VisualizationService(db).get_novel_stats(novel_id)


@router.post('/{novel_id}/invalidate-cache')
def invalidate_cache(
    novel_id: int,
    cache_type: str | None = None,
    db: Session = Depends(get_db),
):
    VisualizationService(db).invalidate_cache(novel_id, cache_type)
    return {'status': 'ok'}
