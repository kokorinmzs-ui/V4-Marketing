"""AI Service — unified entry point for all LLM calls.

All LLM access MUST go through this service.
Direct provider calls are forbidden.
"""

from __future__ import annotations

import json
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
        # Try DeepSeek first
        response = self._deepseek.generate(system_prompt, user_prompt, json_schema)

        if response.status == "success":
            data = self._validate_json(response.data, response.raw_json or "")
            if data["status"] == "success":
                self._total_usage.append(response.usage)
                return AIServiceResponse(
                    status="success",
                    data=data["data"],
                    model_used=response.model_used,
                    usage=response.usage,
                    provider_used="deepseek",
                    elapsed_seconds=response.elapsed_seconds,
                    attempts=1,
                    parsed_json=True,
                )

        # DeepSeek failed — try OpenAI
        openai_response = self._openai.generate(system_prompt, user_prompt, json_schema)
        if openai_response.status == "success":
            data = self._validate_json(openai_response.data, openai_response.raw_json or "")
            if data["status"] == "success":
                self._total_usage.append(openai_response.usage)
                return AIServiceResponse(
                    status="success",
                    data=data["data"],
                    model_used=openai_response.model_used,
                    usage=openai_response.usage,
                    provider_used="openai",
                    elapsed_seconds=openai_response.elapsed_seconds,
                    attempts=2,
                    parsed_json=True,
                )

        # Both failed
        return AIServiceResponse(
            status="error",
            error=f"DeepSeek: {response.error}; OpenAI: {openai_response.error}",
            attempts=2,
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