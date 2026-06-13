"""AI Service — unified entry point for all LLM calls.

All LLM access MUST go through this service.
Direct provider calls are forbidden.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from ai_engine.providers.base import (
    BaseProvider,
    LLMUsage,
    ProviderConfig,
    ProviderResponse,
)
from ai_engine.providers.deepseek import DeepSeekProvider
from ai_engine.providers.openai import OpenAIProvider


@dataclass
class AIServiceConfig:
    """Configuration for AIService."""

    primary_provider: str = field(default_factory=lambda: os.getenv("PRIMARY_LLM_PROVIDER", "deepseek"))
    fallback_provider: str = field(default_factory=lambda: os.getenv("FALLBACK_LLM_PROVIDER", "openai"))
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    timeout_seconds: float = 120.0
    max_retries: int = 3
    retry_delays: tuple[float, ...] = (1.0, 5.0, 15.0)
    mock_mode: bool = False
    mock_response: Optional[dict[str, Any]] = None
    deepseek_mock_response: Optional[dict[str, Any]] = None
    openai_mock_response: Optional[dict[str, Any]] = None


@dataclass
class AIServiceResponse:
    """Response from AIService — always structured, never throws."""

    status: str  # "success" or "error"
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    model_used: str = ""
    usage: LLMUsage = field(default_factory=LLMUsage)
    provider_used: str = ""  # "deepseek" or "openai"
    elapsed_seconds: float = 0.0
    attempts: int = 0
    parsed_json: bool = False


class AIService:
    """Unified AI service with failover DeepSeek → OpenAI.

    Features:
    - Mock mode for testing
    - Retry with backoff (1s → 5s → 15s)
    - Timeout handling
    - JSON parse verification
    - Usage tracking (tokens, cost)
    - Automatic failover from DeepSeek to OpenAI
    - NEVER throws raw exceptions — always returns AIServiceResponse
    """

    def __init__(self, config: Optional[AIServiceConfig] = None):
        self.config = config or AIServiceConfig()

        deepseek_cfg = ProviderConfig(
            api_key=self.config.deepseek_api_key,
            model=self.config.deepseek_model,
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            retry_delays=self.config.retry_delays,
            mock_mode=self.config.mock_mode,
            mock_response=self.config.mock_response,
        )
        openai_cfg = ProviderConfig(
            api_key=self.config.openai_api_key,
            model=self.config.openai_model,
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            retry_delays=self.config.retry_delays,
            mock_mode=self.config.mock_mode,
            mock_response=self.config.mock_response,
        )

        self._deepseek = DeepSeekProvider(deepseek_cfg)
        self._openai = OpenAIProvider(openai_cfg)
        self._providers: dict[str, BaseProvider] = {
            "deepseek": self._deepseek,
            "openai": self._openai,
        }
        self._total_usage: list[LLMUsage] = []

    def generate(
        self,
        system_prompt: str,
        user_prompt: str = "",
        json_schema: Optional[dict[str, Any]] = None,
    ) -> AIServiceResponse:
        """Generate a response with automatic failover DeepSeek → OpenAI.

        Args:
            system_prompt: System-level instructions
            user_prompt: User-level prompt
            json_schema: Optional JSON schema for structured output

        Returns:
            AIServiceResponse with structured data, never throws
        """
        provider_order = self._provider_order()
        last_error = ""
        attempts = 0

        for provider_name in provider_order:
            provider = self._providers.get(provider_name)
            if provider is None:
                continue
            attempts += 1
            response = provider.generate(system_prompt, user_prompt, json_schema)
            last_error = response.error or last_error
            if response.status != "success":
                continue

            data = self._validate_json(response.data, response.raw_json or "")
            if data["status"] != "success":
                last_error = data.get("error", last_error)
                continue

            self._total_usage.append(response.usage)
            return AIServiceResponse(
                status="success",
                data=data["data"],
                model_used=response.model_used,
                usage=response.usage,
                provider_used=provider_name,
                elapsed_seconds=response.elapsed_seconds,
                attempts=attempts,
                parsed_json=True,
            )

        return AIServiceResponse(
            status="error",
            error=last_error or "No provider returned valid JSON",
            attempts=attempts or len(provider_order),
        )

    def _validate_json(self, data: dict[str, Any], raw: str) -> dict[str, Any]:
        """Validate that the response contains valid JSON.

        If data is already a proper dict with expected keys, return it.
        Otherwise try to parse raw string.
        """
        if isinstance(data, dict) and data:
            # Check for common structure
            if "status" in data or "data" in data:
                return {"status": "success", "data": data}
            return {"status": "success", "data": data}

        # Try to parse raw string as JSON
        if raw:
            try:
                parsed = json.loads(raw.strip())
                if isinstance(parsed, dict):
                    return {"status": "success", "data": parsed}
            except (json.JSONDecodeError, ValueError):
                pass

        return {"status": "error", "error": "Response is not valid JSON", "raw": raw[:500]}

    def get_total_usage(self) -> LLMUsage:
        """Get aggregated usage across all calls."""
        total = LLMUsage()
        for u in self._total_usage:
            total.input_tokens += u.input_tokens
            total.output_tokens += u.output_tokens
            total.cost += u.cost
        total.model = "aggregate"
        return total

    def get_call_count(self) -> int:
        """Get total number of LLM calls made."""
        return len(self._total_usage)

    def reset_usage(self) -> None:
        """Reset usage tracking."""
        self._total_usage.clear()

    def _provider_order(self) -> list[str]:
        preferred = self._normalize_provider_name(self.config.primary_provider)
        fallback = self._normalize_provider_name(self.config.fallback_provider)
        order = [preferred, fallback]
        if order[1] == order[0]:
            order.pop()
        return order

    @staticmethod
    def _normalize_provider_name(name: str) -> str:
        normalized = (name or "").strip().lower()
        if normalized in {"deepseek", "openai"}:
            return normalized
        return "deepseek"
