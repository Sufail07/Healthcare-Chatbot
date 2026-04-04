import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import dotenv_values


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://openrouter.ai/api/v1"
    deepseek_model: str = "qwen/qwen3.6-plus:free"
    deepseek_fallback_models: str = "google/gemma-3-4b-it:free,nvidia/nemotron-3-super-120b-a12b:free,stepfun/step-3.5-flash:free"
    database_url: str = "sqlite:///./db/chatbot.db"
    ml_model_path: str = "data/models/disease_model.joblib"
    feature_columns_path: str = "data/models/feature_columns.json"
    
    # JWT Authentication
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    @property
    def all_models(self) -> list[str]:
        """Primary model + fallbacks for rotation on rate limits."""
        models = [self.deepseek_model]
        if self.deepseek_fallback_models:
            models.extend(m.strip() for m in self.deepseek_fallback_models.split(",") if m.strip())
        return models

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    # .env file values take priority over shell env vars
    env_overrides = {k.lower(): v for k, v in dotenv_values(".env").items() if v}
    return Settings(**env_overrides)
