from datetime import datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    webapp_url: str = "http://localhost:5173"

    redis_url: str = "redis://localhost:6379/0"
    ff1_cache_dir: str = "./ff1_cache"

    current_season: int = Field(default_factory=lambda: datetime.now().year)

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    port: int = 0  # hosting platforms set PORT

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def effective_port(self) -> int:
        """Use PORT from hosting platform if set, otherwise api_port."""
        return self.port if self.port else self.api_port

    @property
    def ff1_cache_path(self) -> Path:
        p = Path(self.ff1_cache_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
