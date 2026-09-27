"""Rendering tests. Skipped automatically if discord.py isn't installed."""

import os
import re
import unittest

try:
    import discord  # noqa: F401
except ImportError:  # pragma: no cover
    if os.getenv("REQUIRE_DISCORD"):  # set in CI so these tests can't silently skip
        raise
    discord = None

from invisible_inn import engine
from invisible_inn.content import load_all

from .helpers import CONTENT_DIR


def components(view):
    """The underlying Button/Select objects (DynamicItems wrap them in ``.item``)."""
    return [getattr(c, "item", c) for c in view.children]


@unittest.skipIf(discord is None, "discord.py not installed")
class RenderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from invisible_inn import ui
        self.ui = ui
        self.story = load_all(CONTENT_DIR).stories["invisible_inn"]

    async def test_scene_renders_buttons_with_parseable_ids(self):
        state = engine.new_game(self.story)
        embed, view = self.ui.render_scene(self.story, state, session_id=42)
        self.assertEqual(embed.title, self.story.scene("arrival").title)
        buttons = [c for c in components(view) if isinstance(c, discord.ui.Button)]
        self.assertEqual(len(buttons), 3)
        pattern = re.compile(self.ui.BUTTON_TEMPLATE)
        for b in buttons:
            m = pattern.fullmatch(b.custom_id)
            self.assertIsNotNone(m, b.custom_id)
            self.assertEqual(m["session"], "42")
            self.assertLessEqual(len(b.custom_id), 100)

    async def test_locked_choice_is_disabled(self):
        state = engine.GameState("foyer")
        _, view = self.ui.render_scene(self.story, state, session_id=1)
        door = next(c for c in components(view) if c.custom_id.endswith(":green_door"))
        self.assertTrue(door.disabled)

    async def test_ending_has_no_buttons(self):
        state = engine.GameState("green_room")
        embed, view = self.ui.render_scene(self.story, state, session_id=1)
        self.assertIsNone(view)
        self.assertIn("The End", embed.footer.text)

    async def test_more_than_five_choices_uses_dropdown(self):
        from invisible_inn.content.models import Choice, Scene, Story
        scene = Scene("s", "S", "text", tuple(Choice(f"c{i}", f"Choice {i}", "s") for i in range(7)))
        story = Story("t", "T", "", "s", {"s": scene}, {})
        _, view = self.ui.render_scene(story, engine.new_game(story), session_id=1)
        selects = [c for c in components(view) if isinstance(c, discord.ui.Select)]
        self.assertEqual(len(selects), 1)
        self.assertEqual(len(selects[0].options), 7)

    async def test_role_picker_greys_out_unplayable_roles(self):
        embed, view = self.ui.render_role_picker(self.story, session_id=7)
        self.assertIn("Choose your role", embed.footer.text)
        buttons = {b.custom_id: b for b in components(view)}
        pattern = re.compile(self.ui.ROLE_TEMPLATE)
        for custom_id in buttons:
            self.assertIsNotNone(pattern.fullmatch(custom_id), custom_id)
        self.assertFalse(buttons["inn:r:7:scholar"].disabled)
        self.assertTrue(buttons["inn:r:7:mage"].disabled)
        self.assertIn("coming soon", buttons["inn:r:7:mage"].label)

    async def test_role_choice_shows_tagged_label_and_role_footer(self):
        state = engine.GameState("sign", roles=["scholar"])
        embed, view = self.ui.render_scene(self.story, state, session_id=1)
        labels = [b.label for b in components(view)]
        self.assertIn("[Scholar] Copy the cipher before it fades", labels)
        self.assertIn("condensation cipher", embed.description)
        self.assertIn("Playing as Scholar", embed.footer.text)

    async def test_cog_module_imports(self):
        import invisible_inn.client  # noqa: F401
        import invisible_inn.cogs.adventure  # noqa: F401


if __name__ == "__main__":
    unittest.main()
