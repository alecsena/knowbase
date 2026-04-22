from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Primary LLM
    llm_provider: Literal["anthropic", "openrouter", "openai"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Fallback LLM
    llm_fallback_provider: Literal["anthropic", "openrouter", "openai", ""] = ""
    llm_fallback_model: str = "meta-llama/llama-3.1-70b-instruct"

    # Data providers
    coingecko_api_key: str = ""
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    github_token: str = ""
    defillama_base_url: str = "https://api.llama.fi"

    # Server
    log_level: str = "INFO"
    cache_ttl_seconds: int = 300

    # Scoring
    default_risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"

    # Timeouts / retries
    http_timeout_seconds: int = Field(default=10, ge=1, le=60)
    http_max_retries: int = Field(default=3, ge=0, le=10)


settings = Settings()
