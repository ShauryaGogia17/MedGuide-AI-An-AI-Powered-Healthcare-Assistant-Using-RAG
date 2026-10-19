import os
from functools import lru_cache
from openai import OpenAI
import config  # Loads the root .env before reading configuration.
from llm.errors import AIConfigurationError

@lru_cache(maxsize=2)
def _client_for_key(key: str):
    return OpenAI(api_key=key, timeout=60.0, max_retries=2)

def get_client():
    config.refresh_provider_config()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "your_openai_api_key":
        raise AIConfigurationError('ai_not_configured')
    return _client_for_key(key)

def get_model():
    config.refresh_provider_config()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not model:
        raise AIConfigurationError('ai_model_not_configured')
    return model

def get_embedding_model():
    config.refresh_provider_config()
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
    if not model:
        raise AIConfigurationError('ai_model_not_configured')
    return model
