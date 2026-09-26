"""Simulate button clicks through the Adventure cog with fake Discord objects."""

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

try:
    import discord
except ImportError:  # pragma: no cover
    if os.getenv("REQUIRE_DISCORD"):
        raise
    discord = None

from invisible_inn import engine
from invisible_inn.content import load_all
from invisible_inn.storage import FINISHED, Storage

from .helpers import CONTENT_DIR


def fake_interaction(user_id: int):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=user_id, display_name=f"user{user_id}")
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.channel.send = AsyncMock()
    interaction.message.embeds = [discord.Embed(title="old scene")]
    return interaction


@unittest.skipIf(discord is None, "discord.py not installed")
class AdventureFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from invisible_inn.cogs.adventure import Adventure

        self._tmp = tempfile.TemporaryDirectory()
        storage = Storage(Path(self._tmp.name) / "test.db")
        await storage.setup()
        self.story = load_all(CONTENT_DIR).stories["invisible_inn"]
        self.bot = SimpleNamespace(storage=storage, stories={self.story.id: self.story})
        self.cog = Adventure(self.bot)
        self.session = await storage.create_session(
            guild_id=1, channel_id=2, thread_id=3, owner_id=100,
            story_id=self.story.id, state=engine.new_game(self.story),
        )

    async def asyncTearDown(self):
        self._tmp.cleanup()

    async def click(self, user_id, turn, choice_id):
        interaction = fake_interaction(user_id)
        await self.cog.handle_choice(interaction, self.session.id, turn, choice_id)
        return interaction

    async def test_click_advances_story_and_posts_next_scene(self):
        i = await self.click(100, 0, "step_in")
        i.response.edit_message.assert_awaited_once()
        self.assertIn("chose: Step toward the laughter",
                      i.response.edit_message.call_args.kwargs["embed"].footer.text)
        sent = i.channel.send.call_args.kwargs
        self.assertEqual(sent["embed"].title, "The Foyer")
        self.assertIsNotNone(sent["view"])
        saved = await self.bot.storage.get_session(self.session.id)
        self.assertEqual((saved.state.scene_id, saved.state.turn), ("foyer", 1))

    async def test_other_users_cannot_click(self):
        i = await self.click(999, 0, "step_in")
        self.assertIn("isn't your adventure", i.response.send_message.call_args.args[0])
        i.channel.send.assert_not_awaited()

    async def test_stale_click_is_ignored(self):
        await self.click(100, 0, "step_in")
        i = await self.click(100, 0, "step_in")  # same turn again, e.g. a double-click
        self.assertIn("moment has passed", i.response.send_message.call_args.args[0])

    async def test_locked_choice_is_refused(self):
        await self.click(100, 0, "step_in")
        i = await self.click(100, 1, "green_door")
        self.assertIn("can't do that", i.response.send_message.call_args.args[0])

    async def test_full_playthrough_finishes_session(self):
        for turn, choice in enumerate(["step_in", "take_key", "green_door"]):
            i = await self.click(100, turn, choice)
        self.assertIsNone(i.channel.send.call_args.kwargs["view"])
        saved = await self.bot.storage.get_session(self.session.id)
        self.assertEqual(saved.status, FINISHED)
        i = await self.click(100, 3, "anything")
        self.assertIn("has ended", i.response.send_message.call_args.args[0])

    async def test_dropdown_scene_flow(self):
        from invisible_inn.ui import ChoiceSelect
        for turn, choice in enumerate(["step_in", "ring_bell", "ask_drinks"]):
            i = await self.click(100, turn, choice)
        view = i.channel.send.call_args.kwargs["view"]
        [select] = [c for c in view.children if isinstance(c, ChoiceSelect)]
        values = [o.value for o in select.item.options]
        self.assertIn("cider", values)
        self.assertNotIn("lantern_oil", values)  # needs the lantern; menus hide locked choices

        i = await self.click(100, 3, "cider")
        self.assertIn("tastes of autumn", i.channel.send.call_args.kwargs["embed"].description)
        i = await self.click(100, 4, "leave_bar")
        self.assertEqual(i.channel.send.call_args.kwargs["embed"].title, "The Innkeeper")

    async def test_quit_closes_uncached_thread(self):
        thread = MagicMock(spec=discord.Thread)
        thread.edit = AsyncMock()
        self.bot.get_channel = MagicMock(return_value=None)
        self.bot.fetch_channel = AsyncMock(return_value=thread)
        await self.cog._close_thread(3)
        self.bot.fetch_channel.assert_awaited_once_with(3)
        thread.edit.assert_awaited_once_with(archived=True, locked=True)

    async def test_button_custom_id_round_trips(self):
        from invisible_inn.ui import ChoiceButton
        button = ChoiceButton(self.session.id, 4, "take_key", label="Take")
        match = button.template.fullmatch(button.custom_id)
        rebuilt = await ChoiceButton.from_custom_id(MagicMock(), button.item, match)
        self.assertEqual((rebuilt.session_id, rebuilt.turn, rebuilt.choice_id),
                         (self.session.id, 4, "take_key"))


if __name__ == "__main__":
    unittest.main()
