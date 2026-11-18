"""
OpenAI-Compatible HTTP Client for External LLM Providers in SkillGraph.
Supports OpenAI, Groq, Together AI, Mistral, DeepSeek, Local Ollama, and any
OpenAI-compatible chat completions endpoint with automatic retries, rate-limit backoff,
timeout enforcement, and clean error sanitization.
"""

import json
import time
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from backend.ai.llm.base import (
    LLMProvider,
    LLMProviderError,
    LLMConfigurationError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseError
)

class OpenAICompatibleClient(LLMProvider):
    """
    Client for OpenAI-compatible Chat Completions APIs.
    Communicates via standard HTTP POST /chat/completions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 45,
        max_retries: int = 3,
        provider_name: str = "openai"
    ):
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.provider_name = provider_name

    def is_available(self) -> bool:
        """
        Returns True if the provider has minimum required configuration.
        For commercial cloud providers (OpenAI, Groq, Together), requires an API key.
        For local/custom endpoints (e.g. Ollama or local vLLM), key may be optional.
        """
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            return True
        return bool(self.api_key and self.api_key.strip())

    def get_model_info(self) -> Dict[str, Any]:
        """Returns non-sensitive metadata about the configured provider."""
        masked_key = ""
        if self.api_key:
            masked_key = f"{self.api_key[:4]}...{self.api_key[-3:]}" if len(self.api_key) > 8 else "***"
        return {
            "provider": self.provider_name,
            "model": self.model,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout,
            "max_retries": self.max_retries,
            "has_api_key": bool(self.api_key),
            "masked_key": masked_key,
            "is_configured": self.is_available()
        }

    def _extract_json_block(self, text: str) -> str:
        """Extracts JSON content from raw LLM output, handling markdown code fences."""
        text = text.strip()
        # Look for ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()
        # If no fences, find the outermost { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2500
    ) -> Dict[str, Any]:
        """
        Executes a completion request with retry handling and structured error reporting.
        """
        if not self.is_available():
            raise LLMConfigurationError(
                f"LLM Provider '{self.provider_name}' is not configured. "
                f"Please set LLM_API_KEY or configure a local LLM_BASE_URL."
            )

        endpoint = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SkillGraph-CareerMobility/2.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if json_mode:
            # Most modern providers support json_object mode
            payload["response_format"] = {"type": "json_object"}

        encoded_data = json.dumps(payload).encode("utf-8")
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            start_time = time.time()
            try:
                req = urllib.request.Request(endpoint, data=encoded_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    status_code = response.status
                    raw_body = response.read().decode("utf-8")
                    duration = round(time.time() - start_time, 3)

                    if status_code != 200:
                        raise LLMProviderError(f"Provider returned HTTP status {status_code}: {raw_body}")

                    data = json.loads(raw_body)
                    choices = data.get("choices", [])
                    if not choices:
                        raise LLMResponseError("LLM response contained no choices.")

                    message_content = choices[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})

                    result_payload: Any = message_content
                    if json_mode:
                        clean_json_str = self._extract_json_block(message_content)
                        try:
                            result_payload = json.loads(clean_json_str)
                        except json.JSONDecodeError as jde:
                            raise LLMResponseError(
                                f"Failed to parse LLM response as valid JSON: {jde}\nRaw Content:\n{message_content[:500]}"
                            )

                    return {
                        "content": result_payload,
                        "raw_text": message_content,
                        "model": data.get("model", self.model),
                        "usage": usage,
                        "execution_time": duration,
                        "provider": self.provider_name
                    }

            except urllib.error.HTTPError as he:
                duration = round(time.time() - start_time, 3)
                err_body = ""
                try:
                    err_body = he.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass

                if he.code == 429:
                    # Rate limit encountered
                    last_error = LLMRateLimitError(f"Rate limit exceeded (HTTP 429) from {self.provider_name}: {err_body}")
                    # Exponential backoff
                    sleep_time = (2 ** attempt) * 1.5
                    time.sleep(sleep_time)
                    continue
                elif he.code in (500, 502, 503, 504):
                    # Transient server error
                    last_error = LLMProviderError(f"Transient server error (HTTP {he.code}) from {self.provider_name}: {err_body}")
                    time.sleep(attempt * 1.0)
                    continue
                else:
                    # Non-retriable client error
                    raise LLMProviderError(f"LLM API request failed with HTTP {he.code}: {err_body}")

            except (urllib.error.URLError, TimeoutError) as te:
                duration = round(time.time() - start_time, 3)
                if "timed out" in str(te).lower():
                    last_error = LLMTimeoutError(f"Request to {self.provider_name} timed out after {self.timeout}s.")
                else:
                    last_error = LLMProviderError(f"Network error connecting to {self.provider_name}: {str(te)}")
                time.sleep(attempt * 1.0)
                continue

            except Exception as ex:
                if isinstance(ex, LLMProviderError):
                    raise
                last_error = LLMProviderError(f"Unexpected error calling LLM API: {str(ex)}")
                time.sleep(attempt * 1.0)
                continue

        # If all retries exhausted
        if last_error:
            raise last_error
        raise LLMProviderError(f"Failed to obtain response from {self.provider_name} after {self.max_retries} attempts.")

