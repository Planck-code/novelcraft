from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Unified LLM request across all providers."""

    system_prompt: str
    user_prompt: str
    provider_name: str  # 'openai' | 'deepseek' | 'gemini'
    model_name: str  # 'gpt-4o-mini' | 'deepseek-chat' | 'gemini-2.0-flash'
    temperature: float = 0.3
    max_tokens: int = 4096
    response_format: str | None = None  # 'json_object' for structured output
    extra_params: dict[str, object] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Unified LLM response across all providers."""

    content: str
    provider_name: str
    model_name: str
    usage: dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    finish_reason: str
    raw_response: dict  # full provider response for debugging


class LLMGateway:
    """Unified interface to LLM providers. Hides provider-specific SDK differences."""

    def __init__(self) -> None:
        self._openai: object | None = None
        self._deepseek: object | None = None
        self._gemini: object | None = None

    def _get_openai(self):
        if self._openai is None:
            from app.llm.providers.openai_provider import OpenAIProvider

            self._openai = OpenAIProvider()
        return self._openai

    def _get_deepseek(self):
        if self._deepseek is None:
            from app.llm.providers.openai_provider import OpenAIProvider
            from app.config.settings import settings

            self._deepseek = OpenAIProvider(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )
        return self._deepseek

    def _get_gemini(self):
        if self._gemini is None:
            from app.llm.providers.gemini_provider import GeminiProvider

            self._gemini = GeminiProvider()
        return self._gemini

    def _get_provider(self, provider_name: str):
        if provider_name == 'openai':
            return self._get_openai()
        elif provider_name == 'deepseek':
            return self._get_deepseek()
        elif provider_name == 'gemini':
            return self._get_gemini()
        else:
            raise ValueError(f'Unknown provider: {provider_name}')

    def call(self, request: LLMRequest) -> LLMResponse:
        """Synchronous call. Routes to the correct provider adapter."""
        provider = self._get_provider(request.provider_name)
        logger.info(
            'LLM call: provider=%s model=%s temp=%.2f max_tokens=%d',
            request.provider_name,
            request.model_name,
            request.temperature,
            request.max_tokens,
        )
        return provider.call(request)

    async def acall(self, request: LLMRequest) -> LLMResponse:
        """Async call. Use this in FastAPI async handlers and background tasks."""
        provider = self._get_provider(request.provider_name)
        logger.info(
            'LLM async call: provider=%s model=%s',
            request.provider_name,
            request.model_name,
        )
        return await provider.acall(request)
