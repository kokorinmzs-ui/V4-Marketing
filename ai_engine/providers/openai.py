"""OpenAI Provider — fallback provider when DeepSeek fails."""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from ai_engine.providers.base import BaseProvider, ProviderConfig, ProviderResponse


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI GPT API.

    Used ONLY as fallback when DeepSeek FAILED.
    API key: from env OPENAI_API_KEY or config.
    Model: gpt-4o (default), gpt-4o-mini.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Call OpenAI Chat API with retry logic."""
        if self.config.mock_mode:
            return self._mock_generate(system_prompt, user_prompt)

        return self._retry_with_backoff(
            self._call_api, system_prompt, user_prompt, json_schema
        )

    def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Make a single API call to OpenAI."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return ProviderResponse(
                status="error",
                error="OPENAI_API_KEY not set",
            )

        model = self.config.model or os.getenv("OPENAI_MODEL", "gpt-4o")

        start = time.time()
        try:
            import httpx

            messages = [{"role": "system", "content": system_prompt}]
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})

            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4096,
            }

            if json_schema:
                body["response_format"] = {"type": "json_object"}

            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            result = response.json()
            elapsed = time.time() - start

            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")

            usage_info = result.get("usage", {})
            input_tokens = usage_info.get("prompt_tokens", 0)
            output_tokens = usage_info.get("completion_tokens", 0)
            cost = self._estimate_cost(model, input_tokens, output_tokens)

            parsed = self._parse_json_response(content)
            if parsed.get("status") == "error":
                return ProviderResponse(
                    status="error",
                    error=parsed.get("error", "JSON parse failed"),
                    raw_json=content,
                    usage=self._track_usage(model, input_tokens, output_tokens, cost),
                    model_used=model,
                    elapsed_seconds=elapsed,
                )

            return ProviderResponse(
                status="success",
                data=parsed,
                raw_json=content,
                usage=self._track_usage(model, input_tokens, output_tokens, cost),
                model_used=model,
                elapsed_seconds=elapsed,
            )

        except Exception as e:
            raise  # Let retry_with_backoff handle it

    def _mock_generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> ProviderResponse:
        """Return mock response for testing."""
        mock_data = self.config.mock_response or {
            "status": "success",
            "data": {"mock": True, "message": "Mock OpenAI response"},
        }
        # If mock_response has status=error, return error
        if isinstance(mock_data, dict) and mock_data.get("status") == "error":
            return ProviderResponse(
                status="error",
                error=mock_data.get("error", "Mock OpenAI error"),
                usage=self._track_usage("gpt-4o", 200, 100, 0.00130),
                model_used="gpt-4o (mock)",
                elapsed_seconds=0.01,
            )
        return ProviderResponse(
            status="success",
            data=mock_data,
            usage=self._track_usage("gpt-4o", 200, 100, 0.00130),
            model_used="gpt-4o (mock)",
            elapsed_seconds=0.01,
        )
