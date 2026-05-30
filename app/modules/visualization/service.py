from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infra.db.models.analysis_details import (
    ChapterCharacterMention,
    ChapterEmotionArc,
    ChapterEvent,
)
from app.infra.db.models.chapter import Chapter
from app.infra.db.models.memory import (
    Character,
    CharacterRelation,
    ConsistencyIssue,
    Faction,
    FactionRelation,
    TimelineEvent,
)
from app.infra.db.models.visualization import VisualizationCache

logger = logging.getLogger(__name__)


class VisualizationService:
    """Aggregates data for frontend visualization charts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Character Graph
    # ------------------------------------------------------------------

    def get_character_graph(self, novel_id: int) -> dict:
        """Return nodes + edges for a character relationship graph."""
        characters = (
            self.db.query(Character)
            .filter(Character.novel_id == novel_id)
            .all()
        )

        nodes = []
        for c in characters:
            nodes.append({
                'id': str(c.id),
                'name': c.name,
                'role': c.role or 'unknown',
                'faction_id': c.faction_id,
                'status': c.status or 'alive',
                'first_appearance_chapter_id': c.first_appearance_chapter_id,
            })

        # Add faction nodes
        factions = (
            self.db.query(Faction)
            .filter(Faction.novel_id == novel_id)
            .all()
        )
        for f in factions:
            nodes.append({
                'id': f'faction_{f.id}',
                'name': f.name,
                'role': 'faction',
                'type': f.type or 'other',
                'status': f.status or 'active',
            })

        # Character relations as edges
        edges = []
        relations = (
            self.db.query(CharacterRelation)
            .filter(CharacterRelation.novel_id == novel_id)
            .all()
        )
        for rel in relations:
            edges.append({
                'source': str(rel.character_a_id),
                'target': str(rel.character_b_id),
                'type': rel.relation_type,
                'description': rel.description or '',
            })

        return {'nodes': nodes, 'edges': edges}

    # ------------------------------------------------------------------
    # Emotion Curve
    # ------------------------------------------------------------------

    def get_emotion_curve(
        self, novel_id: int, character_id: int | None = None
    ) -> dict:
        """Return chapter-by-chapter emotion intensity data."""
        chapters = (
            self.db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_no.asc())
            .all()
        )

        chapter_data = []
        for ch in chapters:
            arcs = (
                self.db.query(ChapterEmotionArc)
                .filter(ChapterEmotionArc.chapter_id == ch.id)
                .order_by(ChapterEmotionArc.segment_index.asc())
                .all()
            )

            if arcs:
                # Average intensity for the chapter
                intensities = [a.intensity for a in arcs if a.intensity is not None]
                avg_intensity = sum(intensities) / len(intensities) if intensities else 0.5
                emotions = [a.dominant_emotion for a in arcs if a.dominant_emotion]
            else:
                avg_intensity = 0.5
                emotions = ['neutral']

            chapter_data.append({
                'chapter_no': ch.chapter_no,
                'chapter_id': ch.id,
                'title': ch.title,
                'avg_intensity': round(avg_intensity, 2),
                'dominant_emotions': emotions,
                'segments': [
                    {
                        'label': a.segment_label,
                        'emotion': a.dominant_emotion,
                        'intensity': a.intensity,
                    }
                    for a in arcs
                ],
            })

        return {'chapters': chapter_data}

    # ------------------------------------------------------------------
    # Character Frequency
    # ------------------------------------------------------------------

    def get_character_frequency(self, novel_id: int) -> dict:
        """Return character appearance frequency across chapters."""
        mentions = (
            self.db.query(ChapterCharacterMention)
            .filter(ChapterCharacterMention.novel_id == novel_id)
            .all()
        )

        # Group by character name
        char_map: dict[str, dict] = {}
        for m in mentions:
            name = m.character_name
            if name not in char_map:
                char_map[name] = {
                    'name': name,
                    'character_id': m.character_id,
                    'appearances': 0,
                    'first_chapter_id': m.chapter_id,
                    'roles': set(),
                }
            char_map[name]['appearances'] += 1
            if m.role_in_chapter:
                char_map[name]['roles'].add(m.role_in_chapter)

        # Convert sets to lists for JSON
        result = []
        for data in char_map.values():
            data['roles'] = list(data['roles'])
            result.append(data)

        result.sort(key=lambda x: x['appearances'], reverse=True)
        return {'characters': result[:50]}  # Top 50

    # ------------------------------------------------------------------
    # Faction Evolution
    # ------------------------------------------------------------------

    def get_faction_evolution(self, novel_id: int) -> dict:
        """Return faction-related data for visualization."""
        factions = (
            self.db.query(Faction)
            .filter(Faction.novel_id == novel_id)
            .all()
        )

        faction_data = []
        for f in factions:
            faction_data.append({
                'id': f.id,
                'name': f.name,
                'type': f.type,
                'first_appearance_chapter_id': f.first_appearance_chapter_id,
                'status': f.status,
                'description': f.description,
            })

        relations = (
            self.db.query(FactionRelation)
            .filter(FactionRelation.novel_id == novel_id)
            .all()
        )

        relation_data = []
        for r in relations:
            relation_data.append({
                'faction_a_id': r.faction_a_id,
                'faction_b_id': r.faction_b_id,
                'relation_type': r.relation_type,
                'description': r.description,
            })

        return {'factions': faction_data, 'relations': relation_data}

    # ------------------------------------------------------------------
    # Timeline Data
    # ------------------------------------------------------------------

    def get_timeline_data(self, novel_id: int) -> dict:
        """Return structured timeline data."""
        events = (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.novel_id == novel_id)
            .order_by(TimelineEvent.event_order.asc())
            .all()
        )

        event_data = []
        for e in events:
            event_data.append({
                'id': e.id,
                'name': e.event_name,
                'description': e.description,
                'chapter_id': e.chapter_id,
                'order': e.event_order,
                'type': e.event_type,
                'participants': json.loads(e.participants_json) if e.participants_json else [],
            })

        return {'events': event_data}

    # ------------------------------------------------------------------
    # Overview Stats
    # ------------------------------------------------------------------

    def get_novel_stats(self, novel_id: int) -> dict:
        """Return aggregate statistics for a novel."""
        chapters_count = (
            self.db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .count()
        )

        characters_count = (
            self.db.query(Character)
            .filter(Character.novel_id == novel_id)
            .count()
        )

        factions_count = (
            self.db.query(Faction)
            .filter(Faction.novel_id == novel_id)
            .count()
        )

        issues_count = (
            self.db.query(ConsistencyIssue)
            .filter(
                ConsistencyIssue.novel_id == novel_id,
                ConsistencyIssue.resolution_status == 'open',
            )
            .count()
        )

        events_count = (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.novel_id == novel_id)
            .count()
        )

        return {
            'total_chapters': chapters_count,
            'total_characters': characters_count,
            'total_factions': factions_count,
            'open_consistency_issues': issues_count,
            'timeline_events': events_count,
        }

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------

    def cache_result(
        self, novel_id: int, cache_type: str, cache_key: str, data: dict
    ) -> VisualizationCache:
        """Cache a visualization result."""
        # Remove old cache for same key
        self.db.query(VisualizationCache).filter(
            VisualizationCache.novel_id == novel_id,
            VisualizationCache.cache_type == cache_type,
            VisualizationCache.cache_key == cache_key,
        ).delete()

        cache = VisualizationCache(
            novel_id=novel_id,
            cache_type=cache_type,
            cache_key=cache_key,
            data_json=json.dumps(data, ensure_ascii=False),
            data_version='1',
        )
        self.db.add(cache)
        self.db.commit()
        return cache

    def get_cached(
        self, novel_id: int, cache_type: str, cache_key: str
    ) -> VisualizationCache | None:
        """Get a cached visualization result."""
        return (
            self.db.query(VisualizationCache)
            .filter(
                VisualizationCache.novel_id == novel_id,
                VisualizationCache.cache_type == cache_type,
                VisualizationCache.cache_key == cache_key,
            )
            .one_or_none()
        )

    def invalidate_cache(
        self, novel_id: int, cache_type: str | None = None
    ) -> None:
        """Invalidate visualization cache for a novel."""
        q = self.db.query(VisualizationCache).filter(
            VisualizationCache.novel_id == novel_id
        )
        if cache_type:
            q = q.filter(VisualizationCache.cache_type == cache_type)
        q.delete()
        self.db.commit()
