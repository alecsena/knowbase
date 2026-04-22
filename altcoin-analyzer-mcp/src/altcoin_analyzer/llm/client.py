"""
Multi-provider LLM client with automatic fallback.

Supported providers:
  - anthropic  : Anthropic SDK (Claude models)
  - openrouter : OpenAI-compatible endpoint (any model on OpenRouter)
  - openai     : Official OpenAI SDK (GPT models)

Fallback: if the primary provider raises LLMError, the client retries
the same prompt with the configured fallback provider (if any).
"""

import json
from typing import Any

from altcoin_analyzer.config import settings
from altcoin_analyzer.models.decision import LLMDecision
from altcoin_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Raised when all configured LLM providers fail."""


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return text.strip()


async def _call_anthropic(prompt: str, model: str) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise LLMError("anthropic SDK not installed") from e

    if not settings.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        message = await client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text  # type: ignore[union-attr]
    except Exception as e:
        raise LLMError(f"Anthropic error: {e}") from e


async def _call_openai_compatible(prompt: str, model: str, base_url: str, api_key: str, provider_name: str) -> str:
    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        raise LLMError("openai SDK not installed") from e

    if not api_key:
        raise LLMError(f"{provider_name.upper()}_API_KEY not configured")

    extra_headers: dict[str, str] = {}
    if provider_name == "openrouter":
        extra_headers["HTTP-Referer"] = "https://github.com/altcoin-analyzer-mcp"
        extra_headers["X-Title"] = "Altcoin Analyzer MCP"

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
            extra_headers=extra_headers if extra_headers else None,  # type: ignore[arg-type]
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        raise LLMError(f"{provider_name} error: {e}") from e


async def _dispatch(provider: str, model: str, prompt: str) -> tuple[str, str]:
    """Call the specified provider. Returns (raw_text, provider_label)."""
    if provider == "anthropic":
        text = await _call_anthropic(prompt, model)
        return text, f"anthropic/{model}"

    if provider == "openrouter":
        text = await _call_openai_compatible(
            prompt, model,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            provider_name="openrouter",
        )
        return text, f"openrouter/{model}"

    if provider == "openai":
        text = await _call_openai_compatible(
            prompt, model,
            base_url="https://api.openai.com/v1",
            api_key=settings.openai_api_key,
            provider_name="openai",
        )
        return text, f"openai/{model}"

    raise LLMError(f"Unknown provider: {provider}")


def _resolve_model(provider: str, override_model: str = "") -> str:
    if override_model:
        return override_model
    if provider == "anthropic":
        return settings.anthropic_model
    if provider == "openrouter":
        return settings.openrouter_model
    if provider == "openai":
        return settings.openai_model
    return override_model


class LLMClient:
    """Calls the primary LLM provider; falls back to secondary on failure."""

    async def decide(self, prompt: str) -> tuple[LLMDecision, str]:
        """
        Returns (LLMDecision, provider_label).
        Raises LLMError if both primary and fallback fail.
        """
        primary_provider = settings.llm_provider
        primary_model = _resolve_model(primary_provider)

        raw_text: str | None = None
        provider_label: str | None = None
        primary_error: Exception | None = None

        try:
            raw_text, provider_label = await _dispatch(primary_provider, primary_model, prompt)
            logger.info("llm_call_success", provider=provider_label)
        except LLMError as e:
            primary_error = e
            logger.warning("llm_primary_failed", provider=primary_provider, error=str(e))

        if raw_text is None and settings.llm_fallback_provider:
            fallback_provider = settings.llm_fallback_provider
            fallback_model = _resolve_model(fallback_provider, settings.llm_fallback_model)
            logger.info("llm_fallback_attempt", provider=fallback_provider, model=fallback_model)
            try:
                raw_text, provider_label = await _dispatch(fallback_provider, fallback_model, prompt)
                logger.info("llm_fallback_success", provider=provider_label)
            except LLMError as e:
                raise LLMError(
                    f"Primary ({primary_provider}): {primary_error}. "
                    f"Fallback ({fallback_provider}): {e}"
                ) from e

        if raw_text is None:
            raise LLMError(f"Primary provider {primary_provider} failed: {primary_error}")

        return self._parse(raw_text), provider_label or primary_provider

    def _parse(self, raw: str) -> LLMDecision:
        cleaned = _extract_json(raw)
        try:
            payload: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM returned invalid JSON: {e}\nRaw:\n{raw[:500]}") from e

        # Clamp numeric fields that might be out of range
        if "suggested_allocation_pct" in payload:
            payload["suggested_allocation_pct"] = max(0, min(10, float(payload["suggested_allocation_pct"])))
        if "stop_loss_suggestion_pct" in payload:
            payload["stop_loss_suggestion_pct"] = max(5, min(30, float(payload["stop_loss_suggestion_pct"])))
        if "confidence" in payload:
            payload["confidence"] = max(0.0, min(1.0, float(payload["confidence"])))

        try:
            return LLMDecision.model_validate(payload)
        except Exception as e:
            raise LLMError(f"LLM response failed schema validation: {e}") from e
