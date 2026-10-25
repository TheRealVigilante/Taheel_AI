"""
Resilient Multi-Provider LLM Client with Automatic Fallback.

Primary:
  - Google Gemini (OpenAI-compatible endpoint with GOOGLE_API_KEY)
Fallbacks:
  - OpenRouter (openrouter.ai with configurable OPENROUTER_MODEL)
  - Mistral AI (api.mistral.ai with configurable MISTRAL_MODEL)
"""

from __future__ import annotations
import os
import time
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger("taheel.llm_provider")


class LLMProviderManager:
    """
    Manages LLM client initialization and implements automatic sequential
    failover across Gemini, OpenRouter, and Mistral.
    """

    def __init__(self):
        self.primary_provider = os.getenv("PRIMARY_LLM_PROVIDER", "gemini").lower()
        fallback_str = os.getenv("LLM_FALLBACK_CHAIN", "openrouter,mistral")
        self.fallback_chain = [p.strip().lower() for p in fallback_str.split(",") if p.strip()]

        # Provider configurations
        self.configs: Dict[str, Dict[str, Any]] = {
            "gemini": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
            },
            "mistral": {
                "base_url": "https://api.mistral.ai/v1",
                "api_key": os.getenv("MISTRAL_API_KEY"),
                "model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            },
        }

    def _get_client(self, provider: str) -> Optional[tuple[OpenAI, str]]:
        """Returns initialized OpenAI-compatible client and model name if API key is set."""
        cfg = self.configs.get(provider)
        if not cfg or not cfg["api_key"]:
            return None
        client = OpenAI(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"]
        )
        return client, cfg["model"]

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Executes chat completion attempting primary provider first,
        falling back through the configured chain on error or missing keys.
        """
        # Form attempt sequence
        providers_to_try = [self.primary_provider]
        for fb in self.fallback_chain:
            if fb not in providers_to_try:
                providers_to_try.append(fb)

        errors = []
        for provider in providers_to_try:
            client_tuple = self._get_client(provider)
            if not client_tuple:
                logger.debug("Skipping %s: missing API key or not configured", provider)
                continue

            client, model = client_tuple
            try:
                logger.info(
                    "▶ Calling provider: %s | model: %s | temperature: %.1f",
                    provider, model, temperature
                )
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens

                t_start = time.perf_counter()
                response = client.chat.completions.create(**kwargs)
                elapsed = time.perf_counter() - t_start

                content = response.choices[0].message.content or ""

                # Log token usage if available
                usage = getattr(response, "usage", None)
                if usage:
                    logger.info(
                        "✔ %s responded in %.1fs | prompt_tokens=%s, completion_tokens=%s, total=%s",
                        provider, elapsed,
                        getattr(usage, "prompt_tokens", "?"),
                        getattr(usage, "completion_tokens", "?"),
                        getattr(usage, "total_tokens", "?"),
                    )
                else:
                    logger.info("✔ %s responded in %.1fs", provider, elapsed)
                
                import re
                
                # Clean up markdown code blocks if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                # Strip out <thought>...</thought> tags which reasoning models might inject
                content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL).strip()
                
                if not content:
                    raise ValueError("Received empty content from provider")
                
                return content
            except Exception as exc:
                logger.warning("✘ Provider %s failed (%.1fs): %s. Trying next fallback...",
                               provider, time.perf_counter() - t_start if 't_start' in dir() else 0, str(exc))
                errors.append(f"{provider}: {str(exc)}")

        raise RuntimeError(
            f"All LLM providers in chain failed: {errors}. "
            "Please verify GOOGLE_API_KEY, OPENROUTER_API_KEY, or MISTRAL_API_KEY in your .env file."
        )


# Global singleton instance
llm_manager = LLMProviderManager()
