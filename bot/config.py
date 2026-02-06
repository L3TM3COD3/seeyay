from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(default="")
    
    @field_validator('bot_token', mode='before')
    @classmethod
    def strip_bot_token(cls, v):
        """Удаляем пробелы и переносы из токена"""
        if isinstance(v, str):
            return v.strip()
        return v
    
    # Google Cloud
    gcp_project_id: str = Field(default="")
    gcp_location: str = Field(default="europe-west4")
    
    # Backend
    backend_url: str = Field(default="")
    mini_app_url: str = Field(default="")


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings from environment variables or Secret Manager.
    In Cloud Run, secrets come from mounted volumes or Secret Manager API.
    """
    settings = Settings()
    
    # If bot_token is empty, try to get from Secret Manager
    if not settings.bot_token:
        try:
            from bot.secrets import get_bot_token
            object.__setattr__(settings, 'bot_token', get_bot_token())
        except Exception as e:
            print(f"Warning: Could not get bot token from Secret Manager: {e}")
    
    # If gcp_project_id is empty, try to detect it
    if not settings.gcp_project_id:
        try:
            from bot.secrets import get_gcp_config
            config = get_gcp_config()
            object.__setattr__(settings, 'gcp_project_id', config["project_id"])
            object.__setattr__(settings, 'gcp_location', config["location"])
        except Exception as e:
            print(f"Warning: Could not get GCP config: {e}")
    
    return settings
