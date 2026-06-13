"""DeepSeek Provider — communicates with DeepSeek Chat API."""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from ai_engine.providers.base import BaseProvider, ProviderConfig, ProviderResponse


class DeepSeekProvider(BaseProvider):
    """Provider for DeepSeek Chat API.

    API key: from env DEEPSEEK_API_KEY or config.
    Model: deepseek-chat (default), deepseek-reasoner.
    Base URL: https://api.deepseek.com/v1
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Call DeepSeek Chat API with retry logic.

        In mock mode, returns config.mock_response directly.
        """
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
        """Make a single API call to DeepSeek."""
        api_key = self.config.api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            return ProviderResponse(
                status="error",
                error="DEEPSEEK_API_KEY not set",
            )

        model = self.config.model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        base_url = self.config.base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

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
                "stream": False,
            }

            # If JSON schema is requested, try response_format
            if json_schema:
                body["response_format"] = {"type": "json_object"}

            response = httpx.post(
                f"{base_url}/chat/completions",
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
            elapsed = time.time() - start
            raise  # Let retry_with_backoff handle it

    def _mock_generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> ProviderResponse:
        """Return mock response for testing."""
        mock_data = self.config.mock_response or {
            "status": "success",
            "data": {"mock": True, "message": "Mock DeepSeek response"},
        }
        # If mock_response has status=error, return error
        if isinstance(mock_data, dict) and mock_data.get("status") == "error":
            return ProviderResponse(
                status="error",
                error=mock_data.get("error", "Mock DeepSeek error"),
                usage=self._track_usage("deepseek-chat", 100, 50, 0.000021),
                model_used="deepseek-chat (mock)",
                elapsed_seconds=0.01,
            )
        return ProviderResponse(
            status="success",
            data=mock_data,
            usage=self._track_usage("deepseek-chat", 100, 50, 0.000021),
            model_used="deepseek-chat (mock)",
            elapsed_seconds=0.01,
        )
