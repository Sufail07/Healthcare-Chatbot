import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import dotenv_values
from pathlib import Path


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://openrouter.ai/api/v1"
    deepseek_model: str = "qwen/qwen3.6-plus"
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
        models: list[str] = []
        seen: set[str] = set()

        def add_model(model: str) -> None:
            if model and model not in seen:
                seen.add(model)
                models.append(model)

        raw_models = [self.deepseek_model]
        if self.deepseek_fallback_models:
            raw_models.extend(m.strip() for m in self.deepseek_fallback_models.split(",") if m.strip())

        for raw in raw_models:
            add_model(raw)
            if raw.endswith(":free"):
                add_model(raw.removesuffix(":free"))

        return models

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    # Resolve .env relative to the project root so startup cwd does not matter.
    env_path = Path(__file__).resolve().parent.parent / ".env"
    env_values = dotenv_values(env_path) if env_path.exists() else {}

    # .env file values take priority over shell env vars
    env_overrides = {k.lower(): v for k, v in env_values.items() if v}
    return Settings(**env_overrides)
