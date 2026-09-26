"""Startup checks for the bot. Skipped automatically if discord.py isn't installed."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

try:
    import discord
except ImportError:  # pragma: no cover
    if os.getenv("REQUIRE_DISCORD"):
        raise
    discord = None

from invisible_inn.config import Config, ConfigError

from .helpers import CONTENT_DIR


@unittest.skipIf(discord is None, "discord.py not installed")
class SetupHookTests(unittest.IsolatedAsyncioTestCase):
    async def test_refused_command_sync_gives_friendly_error(self):
        from invisible_inn.client import InnBot

        with tempfile.TemporaryDirectory() as tmp:
            config = Config(token="x", dev_guild_id=123, database_path=Path(tmp) / "t.db",
                            content_dir=CONTENT_DIR, log_level="INFO")
            bot = InnBot(config)
            refused = discord.Forbidden(MagicMock(status=403, reason="Forbidden"), "Missing Access")
            with patch.object(bot.tree, "sync", AsyncMock(side_effect=refused)):
                with self.assertRaises(ConfigError) as ctx:
                    await bot.setup_hook()
            self.assertIn("applications.commands", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
