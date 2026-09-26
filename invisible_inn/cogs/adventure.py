"""Slash commands and choice handling for the adventure."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from .. import engine, ui
from ..storage import ABANDONED, ACTIVE, FINISHED

if TYPE_CHECKING:
    from ..client import InnBot

log = logging.getLogger(__name__)

THREAD_ARCHIVE_MINUTES = 1440  # a day without activity


class Adventure(commands.Cog):
    def __init__(self, bot: "InnBot"):
        self.bot = bot
        # One lock per session so two quick clicks can't both apply.
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock(self, session_id: int) -> asyncio.Lock:
        return self._locks.setdefault(session_id, asyncio.Lock())

    # ------------------------------------------------------------------ /start
    @app_commands.command(name="start", description="Begin a new adventure in a private thread.")
    @app_commands.describe(story="Which story to play (leave blank for the default).")
    @app_commands.guild_only()
    async def start(self, interaction: discord.Interaction, story: str | None = None) -> None:
        stories = self.bot.stories
        story_id = story or next(iter(stories))
        chosen = stories.get(story_id)
        if chosen is None:
            await interaction.response.send_message(f"I don't know a story called `{story_id}`.", ephemeral=True)
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            # From inside a game thread, point the player back to the channel it belongs to.
            parent_id = getattr(channel, "parent_id", None) if isinstance(channel, discord.Thread) else None
            where = f"<#{parent_id}>" if parent_id else "a regular text channel"
            await interaction.response.send_message(
                f"Use `/start` in {where} — I'll open a private thread for your game there.",
                ephemeral=True,
            )
            return

        me = interaction.guild.me  # type: ignore[union-attr]
        perms = channel.permissions_for(me)
        if not (perms.create_private_threads and perms.send_messages_in_threads):
            await interaction.response.send_message(
                "I need the **Create Private Threads** and **Send Messages in Threads** permissions "
                "in this channel. Ask a server admin to grant them.",
                ephemeral=True,
            )
            return

        existing = await self.bot.storage.active_session_for_user(interaction.guild_id, interaction.user.id)
        if existing:
            where = f"<#{existing.thread_id}>" if existing.thread_id else "another channel"
            await interaction.response.send_message(
                f"You already have an adventure in progress in {where}. "
                "Use `/quit` there to end it before starting a new one.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            thread = await channel.create_thread(
                name=f"{chosen.title} · {interaction.user.display_name}"[:100],
                type=discord.ChannelType.private_thread,
                invitable=False,
                auto_archive_duration=THREAD_ARCHIVE_MINUTES,
                reason=f"Adventure started by {interaction.user}",
            )
            await thread.add_user(interaction.user)
        except discord.HTTPException:
            log.exception("Couldn't create a thread in channel %s", channel.id)
            await interaction.followup.send("I couldn't open a thread for your game. Please try again, "
                                            "or ask an admin to check my permissions.", ephemeral=True)
            return

        state = engine.new_game(chosen)
        session = await self.bot.storage.create_session(
            guild_id=interaction.guild_id, channel_id=channel.id, thread_id=thread.id,
            owner_id=interaction.user.id, story_id=chosen.id, state=state,
        )
        log.info("Session %s started by %s in thread %s", session.id, interaction.user.id, thread.id)

        embed, view = ui.render_scene(chosen, state, session.id)
        await thread.send(content=f"{interaction.user.mention}, your adventure begins…", embed=embed, view=view)
        await interaction.followup.send(f"Your adventure awaits in {thread.mention}.", ephemeral=True)

    @start.autocomplete("story")
    async def _story_autocomplete(self, interaction: discord.Interaction, current: str):
        current = current.lower()
        return [
            app_commands.Choice(name=s.title[:100], value=s.id)
            for s in self.bot.stories.values()
            if current in s.title.lower() or current in s.id
        ][:25]

    # -------------------------------------------------------------- /inventory
    @app_commands.command(name="inventory", description="See what you're carrying.")
    @app_commands.guild_only()
    async def inventory(self, interaction: discord.Interaction) -> None:
        session = await self._session_for(interaction)
        if session is None:
            await interaction.response.send_message("You don't have an adventure in progress.", ephemeral=True)
            return
        story = self.bot.stories.get(session.story_id)
        if story is None:
            await interaction.response.send_message("That story is no longer available.", ephemeral=True)
            return
        await interaction.response.send_message(embed=ui.inventory_embed(story, session.state), ephemeral=True)

    # ------------------------------------------------------------------- /quit
    @app_commands.command(name="quit", description="End your current adventure.")
    @app_commands.guild_only()
    async def quit(self, interaction: discord.Interaction) -> None:
        session = await self._session_for(interaction)
        if session is None:
            await interaction.response.send_message("You don't have an adventure in progress.", ephemeral=True)
            return
        if session.owner_id != interaction.user.id:
            await interaction.response.send_message("Only the player who started this adventure can end it.",
                                                    ephemeral=True)
            return
        async with self._lock(session.id):
            await self.bot.storage.set_status(session.id, ABANDONED)
        where = f" in <#{session.channel_id}>" if session.channel_id else ""
        await interaction.response.send_message(f"You leave the inn. This adventure has ended — use `/start`{where} "
                                                "to begin a new one.")
        await self._close_thread(session.thread_id)

    # ------------------------------------------------------------------- /help
    @app_commands.command(name="help", description="How to play.")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="How to play",
            colour=ui.EMBED_COLOUR,
            description=(
                "`/start` — begin an adventure in a private thread\n"
                "`/inventory` — see what you're carrying\n"
                "`/quit` — end your current adventure\n\n"
                "Make choices with the buttons (or the menu) under each scene."
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------------------------------------------------- choice clicks
    async def handle_choice(self, interaction: discord.Interaction, session_id: int, turn: int,
                            choice_id: str) -> None:
        """Called by the buttons/menus in ``ui.py``."""
        async with self._lock(session_id):
            session = await self.bot.storage.get_session(session_id)
            if session is None or session.status != ACTIVE:
                await interaction.response.send_message("This adventure has ended.", ephemeral=True)
                return
            if not await self.bot.storage.is_player(session_id, interaction.user.id):
                await interaction.response.send_message("This isn't your adventure — use `/start` to begin "
                                                        "your own.", ephemeral=True)
                return
            if turn != session.state.turn:
                await interaction.response.send_message("That moment has passed — use the latest message.",
                                                        ephemeral=True)
                return
            story = self.bot.stories.get(session.story_id)
            if story is None:
                await interaction.response.send_message("That story is no longer available.", ephemeral=True)
                return

            try:
                result = engine.choose(story, session.state, choice_id)
            except (engine.ChoiceUnavailable, KeyError):
                await interaction.response.send_message("You can't do that right now.", ephemeral=True)
                return

            await self.bot.storage.save_state(session_id, result.state, FINISHED if result.finished else ACTIVE)

        # Freeze the old message and record what was chosen.
        old_embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else None
        if old_embed:
            old_embed.set_footer(text=f"▶ {interaction.user.display_name} chose: {result.chosen.label}")
        await interaction.response.edit_message(embed=old_embed, view=None)

        embed, view = ui.render_scene(story, result.state, session_id, result)
        await interaction.channel.send(embed=embed, view=view)  # type: ignore[union-attr]

    # ---------------------------------------------------------------- helpers
    async def _session_for(self, interaction: discord.Interaction):
        """The session for this thread, or else the user's active session in this server."""
        if isinstance(interaction.channel, discord.Thread):
            session = await self.bot.storage.get_session_by_thread(interaction.channel.id)
            if session and session.status == ACTIVE and await self.bot.storage.is_player(
                    session.id, interaction.user.id):
                return session
        return await self.bot.storage.active_session_for_user(interaction.guild_id, interaction.user.id)

    async def _close_thread(self, thread_id: int | None) -> None:
        if not thread_id:
            return
        thread = self.bot.get_channel(thread_id)
        if thread is None:
            # Not cached, e.g. after a restart when /quit is used from the parent channel.
            try:
                thread = await self.bot.fetch_channel(thread_id)
            except discord.HTTPException:
                log.warning("Couldn't find thread %s to archive it", thread_id)
                return
        if isinstance(thread, discord.Thread):
            try:
                await thread.edit(archived=True, locked=True)
            except discord.HTTPException:
                log.warning("Couldn't archive thread %s (missing Manage Threads?)", thread_id)


async def setup(bot: "InnBot") -> None:
    await bot.add_cog(Adventure(bot))
