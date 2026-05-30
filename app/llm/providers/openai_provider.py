from __future__ import annotations

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.llm.gateway import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class OpenAIProvider:
    """Adapter for OpenAI and OpenAI-compatible APIs (including DeepSeek)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        from app.config.settings import settings

        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url or None

        if not self.api_key:
            raise ValueError(
                'OpenAI API key not configured. Set OPENAI_API_KEY or DEEPSEEK_API_KEY in environment.'
            )

    def _build_client(self):
        import httpx
        from openai import OpenAI

        # Explicit http_client that ignores system proxy and env vars
        http_client = httpx.Client(
            proxy=None,
            trust_env=False,
            timeout=httpx.Timeout(120.0, connect=30.0),
        )

        kwargs: dict = {'api_key': self.api_key, 'http_client': http_client}
        if self.base_url:
            kwargs['base_url'] = self.base_url
        return OpenAI(**kwargs)

    def call(self, request: LLMRequest) -> LLMResponse:
        """Synchronous call to OpenAI-compatible API."""
        client = self._build_client()

        extra_body = dict(request.extra_params) if request.extra_params else None

        completion = client.chat.completions.create(
            model=request.model_name,
            messages=[
                {'role': 'system', 'content': request.system_prompt},
                {'role': 'user', 'content': request.user_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=(
                {'type': 'json_object'}
                if request.response_format == 'json_object'
                else None
            ),
            extra_body=extra_body,
        )

        choice = completion.choices[0]
        content = choice.message.content or ''

        return LLMResponse(
            content=content,
            provider_name=request.provider_name,
            model_name=request.model_name,
            usage={
                'prompt_tokens': completion.usage.prompt_tokens if completion.usage else 0,
                'completion_tokens': completion.usage.completion_tokens if completion.usage else 0,
                'total_tokens': completion.usage.total_tokens if completion.usage else 0,
            },
            finish_reason=choice.finish_reason or 'unknown',
            raw_response=completion.model_dump(),
        )

    async def acall(self, request: LLMRequest) -> LLMResponse:
        """Async wrapper that runs the sync call in a thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, self.call, request)
