"""
LLM Provider Factory for SkillGraph.
Constructs configured LLM client instances dynamically from environment variables,
supporting seamless provider switching (OpenAI, Groq, Together, Ollama, DeepSeek, Custom).
Never initiates network requests during module import.
"""

import os
from typing import Optional, Dict, Any
from backend.ai.llm.base import LLMProvider, LLMConfigurationError
from backend.ai.llm.client import OpenAICompatibleClient

PROVIDER_DEFAULT_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "ollama": "http://127.0.0.1:11434/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "mistral": "https://api.mistral.ai/v1"
}

PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "groq": "llama-3.3-70b-versatile",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "ollama": "qwen2.5:7b",
    "deepseek": "deepseek-chat",
    "mistral": "mistral-small-latest"
}

def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None
) -> LLMProvider:
    """
    Factory function that instantiates an LLM provider based on parameters or environment variables.
    
    Environment Variables:
        LLM_PROVIDER: Provider name ('openai', 'groq', 'together', 'ollama', 'deepseek', 'custom')
        LLM_MODEL: Model identifier
        LLM_API_KEY: Secret API key
        LLM_BASE_URL: Base HTTP endpoint
        LLM_TIMEOUT: Timeout in seconds (default: 35)
        LLM_MAX_RETRIES: Retry attempts on rate-limit/transient errors (default: 3)
    """
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower().strip()
    
    default_base_url = PROVIDER_DEFAULT_URLS.get(selected_provider, "https://api.openai.com/v1")
    selected_base_url = base_url or os.getenv("LLM_BASE_URL", default_base_url)

    default_model = PROVIDER_DEFAULT_MODELS.get(selected_provider, "gpt-4o-mini")
    selected_model = model or os.getenv("LLM_MODEL", default_model)

    selected_api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "")

    try:
        timeout_val = int(timeout or os.getenv("LLM_TIMEOUT", "35"))
    except ValueError:
        timeout_val = 35

    try:
        retries_val = int(max_retries or os.getenv("LLM_MAX_RETRIES", "3"))
    except ValueError:
        retries_val = 3

    return OpenAICompatibleClient(
        api_key=selected_api_key,
        base_url=selected_base_url,
        model=selected_model,
        timeout=timeout_val,
        max_retries=retries_val,
        provider_name=selected_provider
    )

def get_llm_status() -> Dict[str, Any]:
    """Inspects current LLM configuration and returns availability diagnostics."""
    client = get_llm_client()
    return client.get_model_info()
