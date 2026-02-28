"""EduGuide runtime configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 到 os.environ，否则 pytest 等场景下读不到
_ENV = os.environ
PROJECT_ROOT = Path(__file__).resolve().parent


def _env_int(name: str, default: int) -> int:
    raw = _ENV.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    anthropic_api_key: str
    minimax_api_key: str
    minimax_base_url: str
    minimax_group_id: str
    minimax_homework_vision_model: str
    database_url: str
    redis_url: str
    chroma_host: str
    chroma_port: int
    app_env: str
    log_level: str
    secret_key: str
    github_token: str
    exa_api_key: str
    project_root: Path


SETTINGS = Settings(
    openai_api_key=_ENV.get("OPENAI_API_KEY", ""),
    anthropic_api_key=_ENV.get("ANTHROPIC_API_KEY", ""),
    minimax_api_key=_ENV.get("MINIMAX_API_KEY", ""),
    minimax_base_url=_ENV.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic"),
    minimax_group_id=_ENV.get("MINIMAX_GROUP_ID", ""),
    minimax_homework_vision_model=_ENV.get("MINIMAX_HOMEWORK_VISION_MODEL", "MiniMax-Text-01"),
    database_url=_ENV.get("DATABASE_URL", "postgresql://user:password@localhost:5432/eduguide"),
    redis_url=_ENV.get("REDIS_URL", "redis://localhost:6379/0"),
    chroma_host=_ENV.get("CHROMA_HOST", "localhost"),
    chroma_port=_env_int("CHROMA_PORT", 8001),
    app_env=_ENV.get("APP_ENV", "development"),
    log_level=_ENV.get("LOG_LEVEL", "INFO"),
    secret_key=_ENV.get("SECRET_KEY", "change-me"),
    github_token=_ENV.get("GITHUB_TOKEN", ""),
    exa_api_key=_ENV.get("EXA_API_KEY", ""),
    project_root=PROJECT_ROOT,
)

# Backward-compatible module-level constants.
OPENAI_API_KEY = SETTINGS.openai_api_key
ANTHROPIC_API_KEY = SETTINGS.anthropic_api_key
MINIMAX_API_KEY = SETTINGS.minimax_api_key
MINIMAX_BASE_URL = SETTINGS.minimax_base_url
MINIMAX_GROUP_ID = SETTINGS.minimax_group_id
MINIMAX_HOMEWORK_VISION_MODEL = SETTINGS.minimax_homework_vision_model
DATABASE_URL = SETTINGS.database_url
REDIS_URL = SETTINGS.redis_url
CHROMA_HOST = SETTINGS.chroma_host
CHROMA_PORT = SETTINGS.chroma_port
APP_ENV = SETTINGS.app_env
LOG_LEVEL = SETTINGS.log_level
SECRET_KEY = SETTINGS.secret_key
GITHUB_TOKEN = SETTINGS.github_token
EXA_API_KEY = SETTINGS.exa_api_key
