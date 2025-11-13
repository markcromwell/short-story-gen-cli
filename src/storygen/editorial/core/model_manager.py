"""Model management for AI-powered editorial analysis."""

import asyncio
import time
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..base import ModelError, BudgetExceededError


class CostTracker:
    """Tracks API usage and costs."""

    def __init__(self):
        self.usage_log = []
        self.cost_models = {
            "ollama/qwen3:30b": {"input": 0.0, "output": 0.0},  # Free
            "openai/gpt-4o": {"input": 0.000005, "output": 0.000015},  # $ per token
            "openai/gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
        }

    def record_usage(self, model: str, prompt: str, response: str, duration: float):
        """Record a model usage event."""
        input_tokens = self._count_tokens(prompt)
        output_tokens = self._count_tokens(response)
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        usage_event = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "duration_seconds": duration
        }

        self.usage_log.append(usage_event)

    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        """Get total cost since timestamp."""
        events = self.usage_log
        if since:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) > since]

        return sum(e["cost_usd"] for e in events)

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a usage event."""
        if model not in self.cost_models:
            return 0.0  # Unknown model, assume free

        rates = self.cost_models[model]
        return (input_tokens * rates["input"]) + (output_tokens * rates["output"])

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4


class ModelManager:
    """Manages AI model interactions and cost tracking."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_model = config.get("default_model", "ollama/qwen3:30b")
        self.cost_tracker = CostTracker()
        self.logger = logging.getLogger(__name__)

        # Rate limiting (requests per minute)
        self.rate_limits = {
            "ollama/qwen3:30b": 60,  # Local model, high limit
            "openai/gpt-4o": 10,
            "openai/gpt-4o-mini": 30,
        }
        self.last_request_time = {}

    async def call_model(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Unified interface for model calls."""
        model = model or self.current_model

        # Rate limiting
        await self._wait_if_needed(model)

        # Cost estimation and checking
        estimated_cost = self._estimate_cost(prompt, max_tokens, model)
        if not self._check_budget(estimated_cost):
            raise BudgetExceededError(f"Estimated cost ${estimated_cost:.4f} exceeds budget")

        # Make the call
        start_time = time.time()
        try:
            if model.startswith("ollama/"):
                response = await self._call_ollama(model, prompt, temperature, max_tokens)
            elif model.startswith("openai/"):
                response = await self._call_openai(model, prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported model: {model}")

            # Track usage
            duration = time.time() - start_time
            self.cost_tracker.record_usage(model, prompt, response, duration)

            return response

        except Exception as e:
            self.logger.error(f"Model call failed: {e}")
            raise ModelError(f"Model call failed: {e}") from e

    async def _wait_if_needed(self, model: str):
        """Wait if rate limit would be exceeded."""
        if model not in self.rate_limits:
            return

        limit_per_minute = self.rate_limits[model]
        min_interval = 60 / limit_per_minute

        last_time = self.last_request_time.get(model)
        if last_time:
            elapsed = time.time() - last_time
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)

        self.last_request_time[model] = time.time()

    def _estimate_cost(self, prompt: str, max_tokens: int, model: str) -> float:
        """Estimate cost for a model call."""
        input_tokens = len(prompt) // 4
        output_tokens = max_tokens

        if model not in self.cost_tracker.cost_models:
            return 0.0

        rates = self.cost_tracker.cost_models[model]
        return (input_tokens * rates["input"]) + (output_tokens * rates["output"])

    def _check_budget(self, estimated_cost: float) -> bool:
        """Check if estimated cost is within budget."""
        # For now, always allow - budget checking can be added later
        return True

    async def _call_ollama(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call local Ollama model."""
        # Placeholder - will implement actual Ollama API call
        self.logger.info(f"Calling Ollama model {model} with prompt length {len(prompt)}")

        # Simulate API delay
        await asyncio.sleep(0.1)

        # Return mock response for now
        return f"Mock response from {model} for prompt: {prompt[:100]}..."

    async def _call_openai(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI API."""
        # Placeholder - will implement actual OpenAI API call
        self.logger.info(f"Calling OpenAI model {model} with prompt length {len(prompt)}")

        # Simulate API delay
        await asyncio.sleep(0.2)

        # Return mock response for now
        return f"Mock response from {model} for prompt: {prompt[:100]}..."