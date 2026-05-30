from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.modules.memory_center.service import MemoryCenterService
from app.modules.project_management.service import ProjectManagementService
from app.schemas.memory import (
    CharacterDetailResponse,
    CharacterRelationResponse,
    CharacterResponse,
    CharacterStateResponse,
    ConsistencyIssueResponse,
    FactionResponse,
    GenerateRevisionRequest,
    RealmSystemResponse,
    RevisionSuggestionResponse,
    TimelineEventResponse,
    WorldSettingResponse,
)

router = APIRouter()


# --- Characters ---

@router.get('/novels/{novel_id}/characters', response_model=list[CharacterResponse])
def list_characters(novel_id: int, db: Session = Depends(get_db)) -> list[CharacterResponse]:
    novel = ProjectManagementService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail='小说项目不存在')
    return MemoryCenterService(db).get_characters(novel_id)


@router.get('/novels/{novel_id}/characters/{character_id}', response_model=CharacterDetailResponse)
def get_character(
    novel_id: int, character_id: int, db: Session = Depends(get_db)
) -> CharacterDetailResponse:
    from app.infra.db.models.memory import Character

    char = db.get(Character, character_id)
    if not char or char.novel_id != novel_id:
        raise HTTPException(status_code=404, detail='角色不存在')
    return char


@router.get('/characters/{character_id}/states', response_model=list[CharacterStateResponse])
def get_character_states(
    character_id: int, db: Session = Depends(get_db)
) -> list[CharacterStateResponse]:
    return MemoryCenterService(db).get_character_states(character_id)


@router.get('/novels/{novel_id}/character-relations', response_model=list[CharacterRelationResponse])
def get_character_relations(
    novel_id: int, db: Session = Depends(get_db)
) -> list[CharacterRelationResponse]:
    return MemoryCenterService(db).get_character_relations(novel_id)


# --- Factions ---

@router.get('/novels/{novel_id}/factions', response_model=list[FactionResponse])
def list_factions(novel_id: int, db: Session = Depends(get_db)) -> list[FactionResponse]:
    return MemoryCenterService(db).get_factions(novel_id)


# --- World Settings ---

@router.get('/novels/{novel_id}/world-settings', response_model=list[WorldSettingResponse])
def list_world_settings(
    novel_id: int, category: str | None = None, db: Session = Depends(get_db)
) -> list[WorldSettingResponse]:
    return MemoryCenterService(db).get_world_settings(novel_id, category)


# --- Realm Systems ---

@router.get('/novels/{novel_id}/realm-systems', response_model=list[RealmSystemResponse])
def list_realm_systems(novel_id: int, db: Session = Depends(get_db)) -> list[RealmSystemResponse]:
    return MemoryCenterService(db).get_realm_systems(novel_id)


# --- Timeline ---

@router.get('/novels/{novel_id}/timeline', response_model=list[TimelineEventResponse])
def get_timeline(novel_id: int, db: Session = Depends(get_db)) -> list[TimelineEventResponse]:
    return MemoryCenterService(db).get_timeline(novel_id)


# --- Consistency Issues ---

@router.get('/novels/{novel_id}/consistency-issues', response_model=list[ConsistencyIssueResponse])
def list_consistency_issues(
    novel_id: int, status: str | None = None, db: Session = Depends(get_db)
) -> list[ConsistencyIssueResponse]:
    return MemoryCenterService(db).get_consistency_issues(novel_id, status)


# --- Revision Advice ---

@router.get('/chapters/{chapter_id}/revision-advice', response_model=list[RevisionSuggestionResponse])
def get_revision_advice(
    chapter_id: int, db: Session = Depends(get_db)
) -> list[RevisionSuggestionResponse]:
    from app.modules.revision_advice.service import RevisionAdviceService
    return RevisionAdviceService(db).get_for_chapter(chapter_id)


@router.post('/chapters/{chapter_id}/revision-advice/generate', response_model=list[RevisionSuggestionResponse])
def generate_revision_advice(
    chapter_id: int,
    payload: 'GenerateRevisionRequest',
    db: Session = Depends(get_db),
) -> list[RevisionSuggestionResponse]:
    from app.infra.db.models.chapter import Chapter
    from app.infra.db.models.analysis import ChapterAnalysis
    from app.modules.revision_advice.service import RevisionAdviceService
    from app.schemas.memory import GenerateRevisionRequest as GRR

    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail='章节不存在')

    analysis = db.query(ChapterAnalysis).filter(
        ChapterAnalysis.chapter_id == chapter_id
    ).one_or_none()

    return RevisionAdviceService(db).generate(
        chapter=chapter,
        analysis=analysis,
        provider_name=payload.provider_name,
        model_name=payload.model_name,
    )
