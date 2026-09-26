"""The bot itself: loads content, opens the database, registers commands."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .config import Config
from .content import ContentError, Story, load_all
from .storage import Storage
from .ui import ChoiceButton, ChoiceSelect

log = logging.getLogger(__name__)

EXTENSIONS = ("invisible_inn.cogs.adventure",)


class InnBot(commands.Bot):
    def __init__(self, config: Config):
        # Default intents do NOT include Message Content — we only use slash
        # commands and components, so no privileged intents are needed.
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.config = config
        self.storage = Storage(config.database_path)
        self.stories: dict[str, Story] = {}

    def load_content(self) -> None:
        report = load_all(self.config.content_dir)
        for w in report.warnings:
            log.warning("Content: %s", w)
        if report.errors:
            raise ContentError(report.errors)
        self.stories = report.stories
        log.info("Loaded %d story/stories: %s", len(self.stories), ", ".join(self.stories))

    async def setup_hook(self) -> None:
        self.load_content()
        await self.storage.setup()
        self.add_dynamic_items(ChoiceButton, ChoiceSelect)
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        if self.config.dev_guild_id:
            # Registering to one server makes command changes show up instantly.
            guild = discord.Object(id=self.config.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to dev server %s", len(synced), self.config.dev_guild_id)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands (may take up to an hour to appear)", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, self.user.id if self.user else "?")
