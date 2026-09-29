"""Play the stories at random, as every playable role, and check nothing goes wrong.

These are a fast safety net for writers: a scene where a role has nothing to click,
or a button that belongs to another role, shows up here even if the story checker's
rules can't see it. The walks are seeded, so a failure is repeatable.

(An exhaustive check of every possible playthrough is much slower, about a minute and
a half per role, so it isn't run on every change.)
"""

import random
import unittest

from invisible_inn import engine
from invisible_inn.content import load_all

from .helpers import CONTENT_DIR, REAL_CONTENT_DIR

WALKS = 250
MAX_STEPS = 400


def walk(story, role, rng):
    """One random playthrough. Returns (problems, reached_ending)."""
    state = engine.new_game(story, [role])
    for _ in range(MAX_STEPS):
        scene = story.scene(state.scene_id)
        if scene.ending:
            return [], True
        shown = engine.options_for(story, state)
        problems = [
            f"'{o.choice.id}' in scene '{scene.id}' is shown to the {role} but belongs to another role"
            for o in shown if not o.choice.requires.allows_role(role)
        ]
        clickable = [o.choice.id for o in shown if o.enabled]
        if not clickable:
            problems.append(f"the {role} has nothing to click in scene '{scene.id}'")
        if problems:
            return problems, False
        state = engine.choose(story, state, rng.choice(clickable)).state
    return [], False  # wandered in circles for a long time: not a problem in itself


class PlaythroughTests(unittest.TestCase):
    def check_story(self, content_dir):
        for story in load_all(content_dir).stories.values():
            for role in (r.id for r in story.roles.values() if r.playable):
                rng = random.Random(f"{story.id}:{role}")
                endings = 0
                problems = set()
                for _ in range(WALKS):
                    found, ended = walk(story, role, rng)
                    problems.update(found)
                    endings += ended
                with self.subTest(story=story.id, role=role):
                    self.assertEqual(sorted(problems), [])
                    self.assertGreater(endings, 0, f"no random playthrough as the {role} reached an ending")

    def test_sample_story(self):
        self.check_story(CONTENT_DIR)

    def test_real_story(self):
        self.check_story(REAL_CONTENT_DIR)

    def test_the_walker_notices_a_dead_end(self):
        from invisible_inn.content.models import Choice, Requirements, Role, Scene, Story
        stuck = Scene("s", "S", "t", (Choice("go", "Go", "e", requires=Requirements(flags=("never_set",))),))
        story = Story("t", "T", "", "s", {"s": stuck, "e": Scene("e", "E", "t", ending=True)}, {},
                      roles={"scholar": Role("scholar", "Scholar")})
        problems, ended = walk(story, "scholar", random.Random(1))
        self.assertFalse(ended)
        self.assertEqual(problems, ["the scholar has nothing to click in scene 's'"])

    def test_the_walker_notices_another_roles_button(self):
        from invisible_inn.content.models import Choice, Requirements, Role, Scene, Story
        # A greyed-out choice for the Rogue, wrongly shown to the Scholar (the engine no longer does this).
        scene = Scene("s", "S", "t", (Choice("pick", "Pick", "e", requires=Requirements(roles=("rogue",))),
                                      Choice("read", "Read", "e")))
        story = Story("t", "T", "", "s", {"s": scene, "e": Scene("e", "E", "t", ending=True)}, {},
                      roles={"scholar": Role("scholar", "Scholar"), "rogue": Role("rogue", "Rogue")})
        original = engine.options_for
        try:
            engine.options_for = lambda st, state: [engine.ChoiceOption(c, enabled=False) for c in st.scene(state.scene_id).choices]
            problems, _ = walk(story, "scholar", random.Random(1))
        finally:
            engine.options_for = original
        self.assertIn("'pick' in scene 's' is shown to the scholar but belongs to another role", problems)


if __name__ == "__main__":
    unittest.main()
