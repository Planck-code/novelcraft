# -*- coding: utf-8 -*-
"""Tests for the chapter title recognition and splitting logic."""
from app.modules.novel_import.parser import split_chapters, normalize_text, ParsedChapter


class TestNormalizeText:
    def test_strips_and_normalizes_newlines(self):
        text = '第一章 初入江湖\r\n少年第一次踏入城镇。\n\n'
        result = normalize_text(text)
        assert '\r' not in result
        assert not result.endswith('\n\n')

    def test_handles_mixed_line_endings(self):
        text = 'line1\r\nline2\rline3\nline4'
        result = normalize_text(text)
        assert '\r' not in result
        assert 'line1\nline2\nline3\nline4' in result


class TestSplitChapters:
    def test_standard_chapter_titles(self):
        text = '第一章 初入江湖\n少年\n第二章 风起云涌\n冲突\n第三章 大战\n最终'
        chapters = split_chapters(text)
        assert len(chapters) == 3

    def test_chinese_numeral_chapter_titles(self):
        text = '第一百二十三章 巅峰对决\n强者之间\n第一百二十四章 落幕\n一切'
        chapters = split_chapters(text)
        assert len(chapters) == 2

    def test_arabic_numeral_chapter_titles(self):
        text = '第1章 风起\n故事开始了。\n第2章 云涌\n故事继续。'
        chapters = split_chapters(text)
        assert len(chapters) >= 2

    def test_prologue_and_epilogue(self):
        text = '楔子\n很久以前\n第一章 开始\n故事\n尾声\n一切结束了。'
        chapters = split_chapters(text)
        assert len(chapters) >= 3

    def test_side_story(self):
        text = '第一章 正文\n正文内容。\n番外 中秋特别篇\n番外内容。'
        chapters = split_chapters(text)
        assert len(chapters) >= 2

    def test_no_chapter_headers(self):
        text = 'This is plain text without any chapter headers, should be treated as one chapter.'
        chapters = split_chapters(text)
        assert len(chapters) == 1

    def test_empty_text(self):
        chapters = split_chapters('')
        assert len(chapters) >= 1

    def test_chapter_content_preservation(self):
        text = 'Ch1 Test\nThis is chapter one content.\nWith multiple lines.\n    \nMore content here.\nCh2 Continue\nChapter two content.'
        chapters = split_chapters(text)
        assert len(chapters) >= 1

    def test_chapter_with_volume_info(self):
        text = '第一卷 初入修炼界 第一章 觉醒\n少年\n第二章 入门\n他踏入了宗门。'
        chapters = split_chapters(text)
        assert len(chapters) >= 2


class TestParsedChapter:
    def test_dataclass_fields(self):
        ch = ParsedChapter(title='Test Title', content='Test Content')
        assert ch.title == 'Test Title'
        assert ch.content == 'Test Content'
