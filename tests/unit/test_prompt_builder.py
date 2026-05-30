"""Tests for the prompt builder and loader utilities."""
import pytest
from unittest.mock import patch, mock_open
from app.common.prompt_builder import (
    build_context_block,
    build_output_contract,
    build_full_prompt,
    build_system_prompt,
    build_task_prompt,
)
from app.common.prompt_loader import load_prompt


MOCK_SYSTEM_PROMPT = '你是一个AI助手。'
MOCK_TASK_PROMPT = '请分析以下文本。'


class TestPromptLoader:
    def test_load_prompt_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_prompt('nonexistent/path.txt')


class TestContextBlock:
    def test_builds_with_chapter_text(self):
        result = build_context_block(
            chapter_text='Chapter 1 content text...' * 100,
            max_chars=500,
        )
        assert len(result) > 0
        # The header should be present
        assert '当前章节正文' in result

    def test_builds_with_characters(self):
        chars = [{'name': '张三', 'role': 'protagonist'}]
        result = build_context_block(
            chapter_text='测试文本',
            characters_summary=chars,
            max_chars=2000,
        )
        assert '已知角色信息' in result
        assert '张三' in result

    def test_builds_with_world_settings(self):
        settings = [{'category': 'location', 'name': '青云山'}]
        result = build_context_block(
            chapter_text='测试',
            world_settings_summary=settings,
            max_chars=2000,
        )
        assert '已知世界观设定' in result
        assert '青云山' in result

    def test_builds_with_previous_summaries(self):
        summaries = [
            '第一章摘要: 主角登场。',
            '第二章摘要: 遇到危机。',
        ]
        result = build_context_block(
            chapter_text='测试',
            previous_chapter_summaries=summaries,
            max_chars=2000,
        )
        assert '前文章节摘要' in result
        assert '主角登场' in result

    def test_caps_at_max_chars(self):
        long_text = '长文本' * 5000
        result = build_context_block(chapter_text=long_text, max_chars=1000)
        assert len(result) < 1500

    def test_empty_context(self):
        result = build_context_block(max_chars=1000)
        assert result == ''


class TestOutputContract:
    def test_builds_json_schema_contract(self):
        schema = {
            'type': 'object',
            'required': ['summary'],
            'properties': {
                'summary': {'type': 'string'},
            },
        }
        result = build_output_contract(schema)
        assert '输出格式要求' in result
        assert '"summary"' in result
        assert 'json' in result.lower()


class TestBuildFullPrompt:
    @patch('app.common.prompt_builder.load_prompt')
    def test_assembles_five_layer_prompt(self, mock_load):
        mock_load.side_effect = lambda path: {
            'system/webnovel_analyst_v1.txt': MOCK_SYSTEM_PROMPT,
            'chapter_analysis/chapter_analysis_v1.txt': MOCK_TASK_PROMPT,
        }[path]

        result = build_full_prompt(
            system_prompt_name='system/webnovel_analyst_v1.txt',
            task_prompt_name='chapter_analysis/chapter_analysis_v1.txt',
            context_block='--- 上下文 ---\n测试章节文本',
            output_schema={
                'type': 'object',
                'required': ['summary'],
                'properties': {'summary': {'type': 'string'}},
            },
        )

        assert 'system' in result
        assert 'user' in result
        assert 'output_schema' in result
        assert MOCK_SYSTEM_PROMPT == result['system']
        assert MOCK_TASK_PROMPT in result['user']
        assert '上下文' in result['user']
        assert '输出格式要求' in result['user']


class TestBuildSystemPrompt:
    @patch('app.common.prompt_builder.load_prompt')
    def test_variable_substitution(self, mock_load):
        mock_load.return_value = '你好，{name}！你的任务是{task}。'
        result = build_system_prompt('test.txt', name='测试者', task='分析文本')
        assert '你好，测试者！' in result
        assert '你的任务是分析文本。' in result


class TestBuildTaskPrompt:
    @patch('app.common.prompt_builder.load_prompt')
    def test_task_prompt_with_variables(self, mock_load):
        mock_load.return_value = '请分析{chapter_title}'
        result = build_task_prompt('task.txt', chapter_title='第一章')
        assert '请分析第一章' in result
