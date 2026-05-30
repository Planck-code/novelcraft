from __future__ import annotations

import re
from dataclasses import dataclass


# Matches common Chinese web novel chapter titles:
# - "第X章", "第XX章", "第一百二十三章" (Chinese numerals)
# - "第1章", "第123章" (Arabic numerals)
# - "楔子", "序章", "终章", "尾声", "番外", "后记"
# - Volume markers like "第一卷 第一章 ..."
TITLE_PATTERN = (
    r'^\s*'
    r'(?:'
    r'(?:第\s*[0-9零一二三四五六七八九十百千两]+\s*[卷章节回])\s*'  # Vol/Ch markers
    r'|'
    r'(?:[第序终楔]\s*[^\s]{0,30}?(?:章|节|回|卷|集))'  # Chinese chapter markers
    r'|'
    r'(?:[番外后][^\s]{0,20})'  # Side stories / postscripts
    r'|'
    r'(?:[尾楔终]\s*(?:声|子|章))'  # Epilogue / Prologue variants
    r')'
    r'\s*[^\n]{0,40}'  # Title text (max 40 chars)
    r'\s*$'
)

TITLE_RE = re.compile(TITLE_PATTERN, re.MULTILINE)

# Simpler fallback pattern for just chapter numbers
SIMPLE_TITLE_RE = re.compile(
    r'^\s*(?:第\s*[0-9零一二三四五六七八九十百千两]+\s*章|[序楔尾声终][章节子声]?|番外)',
    re.MULTILINE,
)


@dataclass
class ParsedChapter:
    title: str
    content: str


def normalize_text(text: str) -> str:
    """Normalize line endings and strip surrounding whitespace."""
    # Normalize all line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text.strip()


def split_chapters(text: str) -> list[ParsedChapter]:
    """Split a full novel text into chapters by recognizing chapter titles.

    Uses TITLE_RE to find chapter boundaries, then splits the text
    at those boundaries. Each match becomes a chapter with its title
    as the first line and the rest as body.
    """
    clean_text = normalize_text(text)

    matches = list(TITLE_RE.finditer(clean_text))

    if not matches:
        # No chapter titles found, treat entire text as one chapter
        return [ParsedChapter(title='第1章 未分段', content=clean_text)]

    chapters: list[ParsedChapter] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean_text)

        block = clean_text[start:end].strip()
        lines = [line.strip() for line in block.split('\n') if line.strip()]

        if not lines:
            continue

        title = lines[0]
        body = '\n'.join(lines[1:]).strip()

        chapters.append(ParsedChapter(title=title, content=body))

    if not chapters:
        return [ParsedChapter(title='第1章 未分段', content=clean_text)]

    return chapters
