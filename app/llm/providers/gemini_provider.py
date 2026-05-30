from __future__ import annotations

import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.llm.gateway import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class GeminiProvider:
    """Adapter for Google Gemini API."""

    def __init__(self, api_key: str | None = None) -> None:
        from app.config.settings import settings

        self.api_key = api_key or settings.gemini_api_key

        if not self.api_key:
            raise ValueError(
                'Gemini API key not configured. Set GEMINI_API_KEY in environment.'
            )

    def _build_model(self, model_name: str):
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        generation_config = {
            'temperature': 0.3,
            'max_output_tokens': 4096,
        }

        return genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=None,  # Set per-request
        )

    def call(self, request: LLMRequest) -> LLMResponse:
        """Synchronous call to Gemini API."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        # Gemini combines system prompt into the generation config
        generation_config = {
            'temperature': request.temperature,
            'max_output_tokens': request.max_tokens,
        }

        model = genai.GenerativeModel(
            model_name=request.model_name,
            generation_config=generation_config,
            system_instruction=request.system_prompt,
        )

        # Build the user message
        response = model.generate_content(request.user_prompt)

        # Extract text
        content = response.text or ''

        # Estimate usage (Gemini doesn't always provide detailed token counts)
        usage = {
            'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
            'completion_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
            'total_tokens': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
        }

        # Get finish reason
        finish_reason = 'stop'
        try:
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason)
        except (IndexError, AttributeError):
            pass

        return LLMResponse(
            content=content,
            provider_name=request.provider_name,
            model_name=request.model_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response={'text': content, 'finish_reason': finish_reason},
        )

    async def acall(self, request: LLMRequest) -> LLMResponse:
        """Async wrapper that runs the sync call in a thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, self.call, request)
