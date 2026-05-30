from __future__ import annotations

# ----------------------------------------------------------------
# Shared JSON Schemas for LLM Output Contracts
# ----------------------------------------------------------------
# Each schema defines the expected output structure for a specific
# LLM task. These are used by prompt_builder.build_output_contract()
# and by json_repair.parse_and_repair_json() for validation/repair.
# ----------------------------------------------------------------

CHAPTER_ANALYSIS_SCHEMA: dict = {
    'type': 'object',
    'required': ['summary', 'key_events', 'emotion_overview', 'conflict_summary'],
    'properties': {
        'summary': {
            'type': 'string',
            'description': '本章100-200字的中文剧情摘要',
        },
        'key_events': {
            'type': 'array',
            'description': '3-7个本章关键事件',
            'items': {
                'type': 'object',
                'required': ['event', 'evidence'],
                'properties': {
                    'event': {'type': 'string', 'description': '事件描述'},
                    'evidence': {'type': 'string', 'description': '原文证据摘录'},
                    'participants': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '参与角色名列表',
                    },
                    'event_type': {
                        'type': 'string',
                        'enum': ['plot', 'battle', 'dialogue', 'revelation', 'transition'],
                        'description': '事件类型',
                    },
                },
            },
        },
        'emotion_overview': {
            'type': 'string',
            'description': '本章整体情绪基调和情绪变化描述',
        },
        'conflict_summary': {
            'type': 'string',
            'description': '本章冲突总结（战斗/矛盾/内心挣扎等）',
        },
        'world_building_delta_summary': {
            'type': 'string',
            'description': '本章新增或以其他方式变化的世界观信息',
        },
        'foreshadowing_summary': {
            'type': 'string',
            'description': '本章埋下的伏笔或已回收的伏笔',
        },
        'emotion_arcs': {
            'type': 'array',
            'description': '章节情绪分段变化（可选，最多5段）',
            'items': {
                'type': 'object',
                'required': ['segment_label', 'dominant_emotion', 'intensity'],
                'properties': {
                    'segment_label': {
                        'type': 'string',
                        'enum': ['opening', 'development', 'midpoint', 'climax', 'resolution'],
                    },
                    'dominant_emotion': {
                        'type': 'string',
                        'enum': ['tension', 'excitement', 'calm', 'sadness', 'anger', 'humor', 'suspense', 'triumph'],
                    },
                    'intensity': {
                        'type': 'number',
                        'minimum': 0.0,
                        'maximum': 1.0,
                        'description': '情绪强度 0.0-1.0',
                    },
                    'description': {'type': 'string', 'description': '情绪段描述'},
                },
            },
        },
        'overall_quality_notes': {
            'type': 'string',
            'description': '对本章写作质量的整体观察（节奏、爽点、水文等）',
        },
    },
}

CHARACTER_EXTRACT_SCHEMA: dict = {
    'type': 'object',
    'required': ['characters'],
    'properties': {
        'characters': {
            'type': 'array',
            'description': '本章出场的所有角色',
            'items': {
                'type': 'object',
                'required': ['name', 'role_in_chapter'],
                'properties': {
                    'name': {'type': 'string', 'description': '角色名称'},
                    'aliases': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '本章中出现的该角色别名/称号',
                    },
                    'role_in_chapter': {
                        'type': 'string',
                        'enum': ['protagonist', 'antagonist', 'supporting', 'minor', 'new', 'mentioned'],
                    },
                    'emotional_state': {'type': 'string', 'description': '本章中该角色的情绪状态'},
                    'key_actions': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '本章中该角色的关键行为',
                    },
                    'relationship_changes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['target', 'change'],
                            'properties': {
                                'target': {'type': 'string'},
                                'change': {'type': 'string'},
                                'new_relation_type': {
                                    'type': 'string',
                                    'enum': ['friend', 'enemy', 'lover', 'family', 'master_disciple', 'rival', 'ally', 'neutral'],
                                },
                            },
                        },
                        'description': '关系变化列表',
                    },
                    'physical_state': {'type': 'string', 'description': '身体状态（受伤/完好/突破等）'},
                    'power_level_change': {'type': 'string', 'description': '战力/修为变化描述'},
                    'location': {'type': 'string', 'description': '本章出场地点'},
                },
            },
        },
    },
}

WORLDBUILDING_EXTRACT_SCHEMA: dict = {
    'type': 'object',
    'required': ['world_deltas'],
    'properties': {
        'world_deltas': {
            'type': 'array',
            'description': '本章新增或变化的世界观信息',
            'items': {
                'type': 'object',
                'required': ['category', 'name', 'description', 'is_new'],
                'properties': {
                    'category': {
                        'type': 'string',
                        'enum': ['location', 'item', 'technique', 'realm', 'faction', 'rule', 'history', 'other'],
                    },
                    'name': {'type': 'string', 'description': '设定名称'},
                    'description': {'type': 'string', 'description': '设定描述'},
                    'is_new': {'type': 'boolean', 'description': '是否是全新的设定'},
                    'evidence': {'type': 'string', 'description': '原文证据'},
                },
            },
        },
        'realm_changes': {
            'type': 'array',
            'description': '境界/修为体系变化',
            'items': {
                'type': 'object',
                'required': ['system_name', 'change_description'],
                'properties': {
                    'system_name': {'type': 'string'},
                    'new_tiers': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['name'],
                            'properties': {
                                'order': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'description': {'type': 'string'},
                            },
                        },
                    },
                    'change_description': {'type': 'string'},
                },
            },
        },
        'faction_changes': {
            'type': 'array',
            'description': '势力相关变化',
            'items': {
                'type': 'object',
                'required': ['name', 'description'],
                'properties': {
                    'name': {'type': 'string'},
                    'type': {'type': 'string', 'enum': ['sect', 'family', 'empire', 'kingdom', 'guild', 'academy', 'group', 'other']},
                    'description': {'type': 'string'},
                    'is_new': {'type': 'boolean'},
                    'status': {'type': 'string'},
                },
            },
        },
    },
}

REVISION_ADVICE_SCHEMA: dict = {
    'type': 'object',
    'required': ['advice_items'],
    'properties': {
        'advice_items': {
            'type': 'array',
            'description': '修改建议列表（3-8条）',
            'items': {
                'type': 'object',
                'required': ['category', 'severity', 'title', 'description', 'suggestion'],
                'properties': {
                    'category': {
                        'type': 'string',
                        'enum': [
                            'pacing',
                            'filler_fluff',
                            'logic_issue',
                            'cool_point_opportunity',
                            'emotional_buildup',
                            'power_scaling_collapse',
                            'setting_conflict',
                            'character_consistency',
                            'dialogue_quality',
                            'description_quality',
                            'other',
                        ],
                    },
                    'severity': {
                        'type': 'string',
                        'enum': ['low', 'medium', 'high', 'critical'],
                    },
                    'title': {'type': 'string', 'description': '建议标题（简洁中文）'},
                    'description': {'type': 'string', 'description': '问题描述'},
                    'suggestion': {'type': 'string', 'description': '具体修改建议'},
                    'excerpt': {'type': 'string', 'description': '相关原文摘录（可选）'},
                },
            },
        },
    },
}

MEMORY_UPDATE_SCHEMA: dict = {
    'type': 'object',
    'required': ['new_characters', 'updated_characters', 'new_facts', 'potential_conflicts'],
    'properties': {
        'new_characters': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string'},
                    'aliases': {'type': 'array', 'items': {'type': 'string'}},
                    'role': {'type': 'string', 'enum': ['protagonist', 'antagonist', 'supporting', 'minor', 'cameo']},
                    'summary': {'type': 'string', 'description': '角色简介'},
                    'personality': {'type': 'string', 'description': '性格特征'},
                    'appearance': {'type': 'string', 'description': '外貌描述'},
                    'faction_affiliation': {'type': 'string'},
                    'first_appearance_evidence': {'type': 'string'},
                },
            },
        },
        'updated_characters': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string'},
                    'new_aliases': {'type': 'array', 'items': {'type': 'string'}},
                    'emotional_state_update': {'type': 'string'},
                    'physical_state_update': {'type': 'string'},
                    'power_level_update': {'type': 'string'},
                    'new_location': {'type': 'string'},
                    'summary_update': {'type': 'string'},
                    'status_update': {'type': 'string', 'enum': ['alive', 'dead', 'missing', 'unknown']},
                },
            },
        },
        'new_facts': {
            'type': 'array',
            'description': '本章新增的原子事实',
            'items': {
                'type': 'object',
                'required': ['claim_text', 'claim_type', 'confidence'],
                'properties': {
                    'claim_text': {'type': 'string'},
                    'claim_type': {
                        'type': 'string',
                        'enum': ['character_fact', 'relation_fact', 'faction_fact', 'world_fact', 'realm_fact', 'timeline_fact'],
                    },
                    'confidence': {
                        'type': 'number',
                        'minimum': 0.0,
                        'maximum': 1.0,
                        'description': '该事实的置信度',
                    },
                    'source_excerpt': {'type': 'string'},
                },
            },
        },
        'potential_conflicts': {
            'type': 'array',
            'description': '与已有设定可能存在的冲突',
            'items': {
                'type': 'object',
                'required': ['description', 'severity'],
                'properties': {
                    'description': {'type': 'string'},
                    'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']},
                    'issue_type': {
                        'type': 'string',
                        'enum': ['power_level_contradiction', 'setting_conflict', 'character_behavior_contradiction', 'timeline_contradiction', 'faction_contradiction', 'other'],
                    },
                },
            },
        },
        'timeline_events': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['event_name', 'description'],
                'properties': {
                    'event_name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'event_type': {
                        'type': 'string',
                        'enum': ['major_plot', 'character_milestone', 'world_event', 'revelation', 'battle'],
                    },
                    'participants': {'type': 'array', 'items': {'type': 'string'}},
                },
            },
        },
    },
}

CONSISTENCY_CHECK_SCHEMA: dict = {
    'type': 'object',
    'required': ['issues'],
    'properties': {
        'issues': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['description', 'issue_type', 'severity'],
                'properties': {
                    'description': {'type': 'string'},
                    'issue_type': {
                        'type': 'string',
                        'enum': ['power_level_contradiction', 'setting_conflict', 'character_behavior_contradiction', 'timeline_contradiction', 'faction_contradiction', 'other'],
                    },
                    'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']},
                    'conflicting_claims': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'claim_text': {'type': 'string'},
                                'source_chapter_id': {'type': 'integer'},
                            },
                        },
                    },
                },
            },
        },
    },
}
