"""Settings, read from environment variables (or a local ``.env`` file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    token: str
    dev_guild_id: int | None
    database_path: Path
    content_dir: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        try:
            from dotenv import load_dotenv
        except ImportError:  # python-dotenv is optional in production
            pass
        else:
            load_dotenv()

        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise ConfigError(
                "DISCORD_TOKEN is not set. Copy .env.example to .env and paste the bot token in."
            )

        guild_raw = os.getenv("DEV_GUILD_ID", "").strip()
        try:
            dev_guild_id = int(guild_raw) if guild_raw else None
        except ValueError:
            raise ConfigError(f"DEV_GUILD_ID must be a number (got {guild_raw!r})") from None

        return cls(
            token=token,
            dev_guild_id=dev_guild_id,
            database_path=Path(os.getenv("DATABASE_PATH", "data/invisible_inn.db")),
            content_dir=Path(os.getenv("CONTENT_DIR", "content/stories")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
