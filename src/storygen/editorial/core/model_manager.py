"""Model management for AI-powered editorial analysis."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from ..base import BudgetExceededError, ModelError


class CostTracker:
    """Tracks API usage and costs."""

    def __init__(self):
        self.usage_log = []
        self.cost_models = {
            "ollama/qwen3:30b": {"input": 0.0, "output": 0.0},  # Free
            "openai/gpt-4o": {"input": 0.000005, "output": 0.000015},  # $ per token
            "openai/gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
            "xai/grok-4-fast-non-reasoning": {"input": 0.0, "output": 0.0},  # Free
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
            "duration_seconds": duration,
        }

        self.usage_log.append(usage_event)

    def get_total_cost(self, since: datetime | None = None) -> float:
        """Get total cost since timestamp."""
        events = self.usage_log
        if since:
            events = [e for e in events if datetime.fromisoformat(e["timestamp"]) > since]

        return sum(e["cost_usd"] for e in events)  # type: ignore[no-any-return]

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

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.current_model = config.get("default_model", "xai/grok-4-fast-reasoning")
        self.cost_tracker = CostTracker()
        self.logger = logging.getLogger(__name__)

        # Rate limiting (requests per minute)
        self.rate_limits = {
            "ollama/qwen3:30b": 60,  # Local model, high limit
            "openai/gpt-4o": 10,
            "openai/gpt-4o-mini": 30,
            "xai/grok-4-fast-reasoning": 30,  # xAI rate limit
        }
        self.last_request_time: dict[str, float] = {}

        # Validate API keys are available for configured models
        self._validate_api_keys()

    def _validate_api_keys(self):
        """Validate that required API keys are available."""
        import os

        if self.current_model.startswith("xai/"):
            api_key = os.environ.get("XAI_API_KEY")
            if not api_key:
                raise ValueError("XAI_API_KEY environment variable is required for xAI models")
            if not api_key.startswith("xai-"):
                raise ValueError("XAI_API_KEY appears to be invalid (should start with 'xai-')")

        elif self.current_model.startswith("openai/"):
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required for OpenAI models"
                )
            if not api_key.startswith("sk-"):
                raise ValueError("OPENAI_API_KEY appears to be invalid (should start with 'sk-')")

        # Ollama doesn't require API keys
        elif self.current_model.startswith("ollama/"):
            pass

        else:
            self.logger.warning(f"No API key validation available for model: {self.current_model}")

    async def call_model(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str | None = None,
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
            elif model.startswith("xai/"):
                response = await self._call_xai(model, prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported model: {model}")

            # Track usage
            duration = time.time() - start_time
            self.cost_tracker.record_usage(model, prompt, response, duration)

            return response

        except Exception as e:
            self.logger.error(f"Model call failed: {e}")
            raise ModelError(f"Model call failed: {e}") from e

    def call_model_sync(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str | None = None,
    ) -> str:
        """Synchronous wrapper for model calls."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use run_until_complete in a thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.call_model(prompt, temperature, max_tokens, model)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.call_model(prompt, temperature, max_tokens, model)
                )
        except RuntimeError:
            # No event loop, create a new one
            return asyncio.run(self.call_model(prompt, temperature, max_tokens, model))

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

    async def _call_ollama(
        self, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call local Ollama model."""
        try:
            import litellm

            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content  # type: ignore[no-any-return]
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            raise ModelError(f"Ollama API call failed: {e}") from e

    async def _call_openai(
        self, model: str, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call OpenAI API."""
        try:
            import litellm

            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content  # type: ignore[no-any-return]
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            raise ModelError(f"OpenAI API call failed: {e}") from e

    async def _call_xai(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call xAI API using litellm."""
        try:
            import litellm

            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content  # type: ignore[no-any-return]
        except Exception as e:
            self.logger.error(f"xAI API call failed: {e}")
            raise ModelError(f"xAI API call failed: {e}") from e
