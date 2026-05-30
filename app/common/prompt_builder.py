from __future__ import annotations

import json

from app.common.prompt_loader import load_prompt


def build_system_prompt(prompt_name: str, **overrides: str) -> str:
    """Load a system prompt template and apply variable substitution.

    Args:
        prompt_name: Relative path within prompts/, e.g. 'system/webnovel_analyst_v1.txt'
        **overrides: Key-value pairs for template variable substitution.
                     Variables in the template use {key} format.
    """
    template = load_prompt(prompt_name)
    for key, value in overrides.items():
        template = template.replace('{' + key + '}', value)
    return template


def build_task_prompt(prompt_name: str, **variables: str) -> str:
    """Load a task-prompt template and apply variable substitution."""
    return build_system_prompt(prompt_name, **variables)


def build_context_block(
    chapter_text: str = '',
    characters_summary: list[dict] | None = None,
    recent_events: list[dict] | None = None,
    world_settings_summary: list[dict] | None = None,
    previous_chapter_summaries: list[str] | None = None,
    max_chars: int | None = None,
) -> str:
    """Build the Context Prompt block by assembling minimal necessary context.

    Hard-capped at max_chars (from settings.max_context_chars if not specified).
    """
    from app.config.settings import settings

    if max_chars is None:
        max_chars = settings.max_context_chars

    sections: list[str] = []
    total_chars = 0

    # 1. Current chapter text (highest priority)
    if chapter_text:
        text_header = '--- 当前章节正文 ---\n'
        remaining = max_chars - total_chars - len(text_header)
        if remaining > 50:
            clipped = chapter_text[:remaining]
            sections.append(text_header + clipped)
            total_chars += len(text_header) + len(clipped)

    # 2. Previous chapter summaries
    if previous_chapter_summaries and total_chars < max_chars:
        header = '--- 前文章节摘要 ---\n'
        remaining = max_chars - total_chars - len(header)
        if remaining > 200:
            summaries_text = ''
            for s in previous_chapter_summaries:
                if len(summaries_text) + len(s) + 2 > remaining:
                    break
                summaries_text += s + '\n'
            if summaries_text:
                sections.append(header + summaries_text.strip())
                total_chars += len(header) + len(summaries_text)

    # 3. Character context
    if characters_summary and total_chars < max_chars:
        header = '--- 已知角色信息 ---\n'
        remaining = max_chars - total_chars - len(header)
        if remaining > 200:
            chars_text = json.dumps(characters_summary, ensure_ascii=False, indent=2)
            if len(chars_text) > remaining:
                chars_text = chars_text[:remaining]
            sections.append(header + chars_text)
            total_chars += len(header) + len(chars_text)

    # 4. World settings context
    if world_settings_summary and total_chars < max_chars:
        header = '--- 已知世界观设定 ---\n'
        remaining = max_chars - total_chars - len(header)
        if remaining > 200:
            world_text = json.dumps(world_settings_summary, ensure_ascii=False, indent=2)
            if len(world_text) > remaining:
                world_text = world_text[:remaining]
            sections.append(header + world_text)
            total_chars += len(header) + len(world_text)

    # 5. Recent events
    if recent_events and total_chars < max_chars:
        header = '--- 最近事件 ---\n'
        remaining = max_chars - total_chars - len(header)
        if remaining > 200:
            events_text = json.dumps(recent_events, ensure_ascii=False, indent=2)
            if len(events_text) > remaining:
                events_text = events_text[:remaining]
            sections.append(header + events_text)

    return '\n\n'.join(sections)


def build_output_contract(schema: dict) -> str:
    """Generate the Output Contract section from a JSON Schema dict."""
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
    return f"""--- 输出格式要求 ---
请严格按以下JSON Schema格式返回结果，不要包含任何其他文字和解释：

{schema_json}

请确保:
1. 所有必填字段都存在
2. 字段类型正确
3. 字符串使用中文
4. 直接返回JSON，不包含markdown代码块标记"""


def build_full_prompt(
    system_prompt_name: str,
    task_prompt_name: str,
    context_block: str,
    output_schema: dict,
    task_variables: dict[str, str] | None = None,
) -> dict:
    """Assemble the 5-layer prompt: System -> Task -> Context -> Output Contract.

    Returns a dict with keys: 'system', 'user', 'output_schema' suitable for
    passing to the unified LLM gateway.
    """
    system = load_prompt(system_prompt_name)
    task = load_prompt(task_prompt_name)

    if task_variables:
        for key, value in task_variables.items():
            task = task.replace('{' + key + '}', value)

    output_contract = build_output_contract(output_schema)

    user_prompt_parts = [task]
    if context_block:
        user_prompt_parts.append(context_block)
    user_prompt_parts.append(output_contract)

    user = '\n\n'.join(user_prompt_parts)

    return {
        'system': system,
        'user': user,
        'output_schema': output_schema,
    }
