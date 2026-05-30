from __future__ import annotations

from pathlib import Path

from app.config.settings import settings


def load_prompt(prompt_path: str) -> str:
    """Load a prompt template from the prompts/ directory.

    Args:
        prompt_path: Relative path within prompts/, e.g.
                     'system/webnovel_analyst_v1.txt'

    Returns the prompt text as a string.
    Raises FileNotFoundError if the path doesn't exist.
    """
    full_path = settings.prompts_dir / prompt_path
    if not full_path.exists():
        raise FileNotFoundError(f'Prompt template not found: {full_path}')
    return full_path.read_text(encoding='utf-8').strip()
