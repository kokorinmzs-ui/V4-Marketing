"""Base provider and shared models for AI providers."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMUsage:
    """Tracks token usage and cost for a single LLM call."""

    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0

    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ProviderResponse:
    """Standardised response from any provider."""

    status: str  # "success" or "error"
    data: dict[str, Any] = field(default_factory=dict)
    raw_json: Optional[str] = None
    error: str = ""
    usage: LLMUsage = field(default_factory=LLMUsage)
    model_used: str = ""
    elapsed_seconds: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""

    api_key: str = ""
    model: str = ""
    base_url: str = ""
    timeout_seconds: float = 120.0
    max_retries: int = 3
    retry_delays: tuple[float, ...] = (1.0, 5.0, 15.0)
    mock_mode: bool = False
    mock_response: Optional[dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base for all LLM providers.

    All providers MUST be called through AIService — never directly.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate a response from the LLM.

        Args:
            system_prompt: The system-level instructions
            user_prompt: The user-level prompt
            json_schema: Optional JSON schema for structured output

        Returns:
            ProviderResponse with status, data, usage tracking
        """
        ...

    def _parse_json_response(self, raw: str) -> dict[str, Any]:
        """Parse a raw string response into JSON.

        Returns {"status": "error", "error": "..."} on failure.
        """
        text = raw.strip()
        # Try to extract JSON from markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last ``` lines
            json_lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(json_lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"JSON decode failed: {e}", "raw": raw[:500]}

    def _track_usage(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ) -> LLMUsage:
        return LLMUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on model pricing (USD)."""
        rates = {
            "deepseek-chat": (0.14, 0.28),  # per 1M tokens
            "deepseek-reasoner": (0.55, 2.19),
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.15, 0.60),
        }
        input_rate, output_rate = rates.get(model, (0.0, 0.0))
        cost = (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
        return round(cost, 6)

    def _retry_with_backoff(self, func, *args, **kwargs) -> ProviderResponse:
        """Execute a function with retry logic."""
        last_error = ""
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.config.retry_delays[min(attempt - 1, len(self.config.retry_delays) - 1)]
                    time.sleep(delay)
                return func(*args, **kwargs)
            except Exception as e:
                last_error = str(e)
                if attempt < self.config.max_retries:
                    continue
        return ProviderResponse(
            status="error",
            error=f"All {self.config.max_retries + 1} attempts failed. Last error: {last_error}",
        )