from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChapterText:
    """Clean chapter text ready for analysis."""
    novel_id: int
    chapter_no: int
    title: str
    clean_text: str
    word_count: int


@dataclass
class ChapterAnalysisResult:
    """Output of a completed chapter analysis, before DB persistence."""
    chapter_id: int
    summary: str
    emotion_overview: str
    battle_conflict_summary: str
    world_building_delta_summary: str
    foreshadowing_summary: str
    structured_json: dict
    provider_name: str
    model_name: str
    prompt_version: str
    raw_response_text: str


@dataclass
class RevisionAdviceResult:
    """Output of revision advice generation."""
    chapter_id: int
    advice_items: list[dict] = field(default_factory=list)
    raw_response_text: str = ''


@dataclass
class MemoryUpdateResult:
    """Summary of changes made to long-term memory."""
    new_characters: list[dict] = field(default_factory=list)
    updated_characters: list[dict] = field(default_factory=list)
    new_factions: list[dict] = field(default_factory=list)
    new_world_settings: list[dict] = field(default_factory=list)
    new_timeline_events: list[dict] = field(default_factory=list)
    conflicts_found: list[dict] = field(default_factory=list)


@dataclass
class WorkflowOptions:
    """Options controlling which steps a workflow executes."""
    include_revision: bool = True
    update_memory: bool = True
    check_consistency: bool = False
    force_reanalyze: bool = False
