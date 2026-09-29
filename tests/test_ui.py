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

    async def test_new_and_completed_quests_are_announced(self):
        state = engine.new_game(self.story, ["scholar"])
        result = engine.choose(self.story, state, "step_in")
        embed, _ = self.ui.render_scene(self.story, result.state, 1, result)
        quests = next(f for f in embed.fields if f.name == "Quests")
        self.assertIn("New quest: **Who Runs This Place?**", quests.value)
        result = engine.choose(self.story, result.state, "ring_bell")
        embed, _ = self.ui.render_scene(self.story, result.state, 1, result)
        self.assertIn("Quest complete", next(f for f in embed.fields if f.name == "Quests").value)

    async def test_other_roles_secret_quests_are_not_announced(self):
        from invisible_inn.engine import ChoiceResult
        state = engine.GameState("foyer", roles=["rogue"], quests={"decode_the_sign": engine.QUEST_ACTIVE,
                                                                   "find_the_innkeeper": engine.QUEST_ACTIVE})
        scene = self.story.scene("foyer")
        result = ChoiceResult(state=state, scene=scene, chosen=scene.choices[0], gained=(), lost=(),
                              quests_started=("decode_the_sign", "find_the_innkeeper"))
        embed = self.ui.scene_embed(self.story, state, result)
        quests = next(f for f in embed.fields if f.name == "Quests").value
        self.assertIn("Who Runs This Place?", quests)
        self.assertNotIn("Vanishing Letters", quests, "the Scholar's secret quest must not leak to the Rogue")

        result = ChoiceResult(state=state, scene=scene, chosen=scene.choices[0], gained=(), lost=(),
                              quests_completed=("decode_the_sign",))
        embed = self.ui.scene_embed(self.story, state, result)
        self.assertNotIn("Quests", [f.name for f in embed.fields], "nothing visible, so no Quests box")

    async def test_quests_card(self):
        empty = self.ui.quests_embed(self.story, engine.new_game(self.story, ["scholar"]))
        self.assertIn("haven't discovered any quests", empty.description)
        state = engine.GameState("foyer", roles=["scholar"], quests={
            "find_the_innkeeper": engine.QUEST_COMPLETED, "decode_the_sign": engine.QUEST_ACTIVE,
        })
        embed = self.ui.quests_embed(self.story, state)
        names = [f.name for f in embed.fields]
        self.assertEqual(names, ["📜 The Vanishing Letters · secret", "Completed"])
        self.assertIn("Who Runs This Place?", embed.fields[1].value)

    async def test_quests_card_stays_within_discord_limits(self):
        from invisible_inn.content.models import Quest, Story
        quests = {f"q{i}": Quest(f"q{i}", f"Quest number {i} " + "x" * 60, "d" * 1000) for i in range(60)}
        story = Story("t", "T", "", "s", {}, {}, quests=quests)
        state = engine.GameState("s", quests={q: (engine.QUEST_ACTIVE if i % 2 else engine.QUEST_COMPLETED)
                                               for i, q in enumerate(quests)})
        embed = self.ui.quests_embed(story, state)
        self.assertLessEqual(len(embed.fields), 25)
        self.assertLessEqual(len(embed), 6000)
        self.assertTrue(all(len(f.value) <= 1024 for f in embed.fields))
        self.assertIn("Completed", [f.name for f in embed.fields])

    async def test_result_text_goes_at_the_bottom_in_italics(self):
        state = engine.new_game(self.story)
        result = engine.choose(self.story, state, "step_in")
        result = engine.choose(self.story, result.state, "take_key")
        text = self.ui.scene_embed(self.story, result.state, result).description
        scene_part, outcome = text.split("\n\n---\n\n")
        self.assertTrue(scene_part.startswith("The moment you cross the threshold"))
        self.assertEqual(outcome, "*You lift the key from its hook. Nobody stops you.*")

    async def test_scene_shows_the_roles_own_result_text(self):
        for roles, expected in ((["rogue"], "before anyone notices the hook"), (["scholar"], "Nobody stops you.*")):
            state = engine.GameState("foyer", roles=roles)
            result = engine.choose(self.story, state, "take_key")
            text = self.ui.scene_embed(self.story, result.state, result).description
            self.assertIn(expected, text.split("\n\n---\n\n")[1])

    async def test_italicise_handles_asterisks_and_line_breaks(self):
        text = 'The frame says *"Shelter for those who\nneed it."* Also: **wipe your feet**.\n\nSecond line.'
        self.assertEqual(self.ui.italicise(text),
                         '*The frame says "Shelter for those who need it." Also: **wipe your feet**.*\n\n'
                         '*Second line.*')

    async def test_reflow_joins_wrapped_lines_but_keeps_structure(self):
        text = "One line\nwrapped.\n\n> quoted\n> text\n>\n> more\n\n- item one\n- item two"
        self.assertEqual(self.ui.reflow(text),
                         "One line wrapped.\n\n> quoted text\n> more\n\n- item one\n- item two")

    async def test_long_scene_text_is_trimmed_but_result_text_is_kept(self):
        from invisible_inn.content.models import Choice, Scene, Story
        scene = Scene("s", "S", "word " * 900, (Choice("go", "Go", "s", result_text="It happened."),))
        story = Story("t", "T", "", "s", {"s": scene}, {})
        result = engine.choose(story, engine.new_game(story), "go")
        text = self.ui.scene_embed(story, result.state, result).description
        self.assertLessEqual(len(text), 4096)
        self.assertTrue(text.endswith("*It happened.*"))

    async def test_cog_module_imports(self):
        import invisible_inn.client  # noqa: F401
        import invisible_inn.cogs.adventure  # noqa: F401


if __name__ == "__main__":
    unittest.main()
