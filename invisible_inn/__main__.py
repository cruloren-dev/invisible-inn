"""Run the bot: ``python -m invisible_inn``."""

from __future__ import annotations

import logging
import sys

from .config import Config, ConfigError
from .content import ContentError


def main() -> int:
    try:
        config = Config.from_env()
    except ConfigError as exc:
        print(f"Configuration problem: {exc}", file=sys.stderr)
        return 1

    import discord

    from .client import InnBot

    discord.utils.setup_logging(level=getattr(logging, config.log_level, logging.INFO))
    bot = InnBot(config)
    try:
        bot.run(config.token, log_handler=None)
    except ContentError as exc:
        print("Story content has errors — fix them and restart:", file=sys.stderr)
        for err in exc.errors:
            print(f"  ✘ {err}", file=sys.stderr)
        return 1
    except ConfigError as exc:
        print(f"Configuration problem: {exc}", file=sys.stderr)
        return 1
    except discord.LoginFailure:
        print("Discord rejected the token. Check DISCORD_TOKEN in your .env file.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
