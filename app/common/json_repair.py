from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


class JSONRepairError(Exception):
    """Raised when JSON parsing fails after all repair attempts."""

    def __init__(self, raw_text: str, cause: Exception | None = None) -> None:
        self.raw_text = raw_text
        self.cause = cause
        preview = raw_text[:200].replace('\n', ' ')
        msg = f'Failed to parse JSON after repair attempts. Preview: {preview}...'
        if cause:
            msg += f' Caused by: {cause}'
        super().__init__(msg)


def parse_and_repair_json(raw_response: str, expected_schema: dict | None = None) -> dict:
    """Attempt to parse JSON from an LLM response string.

    Strategy (tried in order):
    1. Try json.loads directly.
    2. Extract JSON from markdown code fences (```json ... ``` or ``` ... ```).
    3. Extract JSON between first { and last } (or first [ and last ]).
    4. Attempt to repair truncated JSON by auto-closing brackets/braces.
    5. If expected_schema is provided, validate key presence and fill
       missing keys with None/defaults from the schema.

    Returns a dict. Never returns None. Raises JSONRepairError on failure.
    """
    text = raw_response.strip()

    # Strategy 1: Direct parse
    result = _try_json_parse(text)
    if result is not None:
        return result

    # Strategy 2: Extract from markdown code fences
    fence_pattern = re.compile(r'```(?:json)?\s*\n(.*?)\n```', re.DOTALL)
    fences = fence_pattern.findall(text)
    for fenced in fences:
        result = _try_json_parse(fenced.strip())
        if result is not None:
            return result

    # Strategy 3 & 4: Extract between braces + auto-close truncated brackets
    for brace_open, brace_close in [('{', '}'), ('[', ']')]:
        start = text.find(brace_open)
        if start == -1:
            continue
        end = text.rfind(brace_close)
        if end > start:
            extracted = text[start:end + 1]
            result = _try_json_parse(extracted)
            if result is not None:
                return result

            # Try to repair
            repaired = _repair_truncated(extracted, brace_open, brace_close)
            if repaired and repaired != extracted:
                result = _try_json_parse(repaired)
                if result is not None:
                    logger.info('JSON repaired via auto-closing brackets')
                    return result
        else:
            # No closing brace found at all - try to repair from start
            extracted = text[start:]
            repaired = _repair_truncated(extracted, brace_open, brace_close)
            if repaired:
                result = _try_json_parse(repaired)
                if result is not None:
                    logger.info('JSON repaired via auto-closing truncated brackets')
                    return result

    # Strategy 5: Schema-guided fill
    if expected_schema:
        partial = _extract_partial_json(text, expected_schema)
        if partial:
            logger.info('JSON partially recovered with schema defaults')
            return partial

    raise JSONRepairError(raw_response)


def _try_json_parse(text: str) -> dict | list | None:
    """Try to parse text as JSON. Returns None on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _repair_truncated(text: str, open_char: str, close_char: str) -> str | None:
    """Attempt to repair truncated JSON by auto-closing unclosed brackets and braces."""
    if not text:
        return None

    # Count unbalanced brackets/braces
    stack: list[str] = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append(ch)
        elif ch == '}':
            if stack and stack[-1] == '{':
                stack.pop()
        elif ch == ']':
            if stack and stack[-1] == '[':
                stack.pop()

    if not stack:
        return None

    # Build closing sequence
    closing = ''
    for opener in reversed(stack):
        if opener == '{':
            closing += '}'
        elif opener == '[':
            closing += ']'

    # Also close any unclosed string
    # Count quotes to check if we're in a string
    quote_count = text.count('"') - text.count('\\"')
    if quote_count % 2 != 0:
        text = text + '"'

    return text + closing


def _extract_partial_json(text: str, schema: dict) -> dict | None:
    """Extract whatever key-value pairs we can find and fill missing ones from schema defaults."""
    properties = schema.get('properties', {})
    required_keys = schema.get('required', list(properties.keys()))

    result: dict = {}

    for key in required_keys:
        prop_schema = properties.get(key, {})
        default = _schema_default(prop_schema)
        result[key] = default

    # Try to parse whatever we can extract
    partial = None
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        partial = _try_json_parse(text[start:end + 1])

    if partial and isinstance(partial, dict):
        result.update(partial)

    # Check if we have at least some required keys
    has_any = any(result.get(k) is not None for k in required_keys)
    return result if has_any else None


def _schema_default(prop_schema: dict) -> object:
    """Get the default value for a JSON Schema property."""
    if 'default' in prop_schema:
        return prop_schema['default']

    type_map = {
        'string': '',
        'array': [],
        'object': {},
        'number': 0,
        'integer': 0,
        'boolean': False,
    }
    prop_type = prop_schema.get('type', 'string')
    return type_map.get(prop_type, None)
