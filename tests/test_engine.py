import unittest

from invisible_inn import engine
from invisible_inn.content import load_all

from .helpers import CONTENT_DIR


def sample_story():
    return load_all(CONTENT_DIR).stories["invisible_inn"]


def ids(options):
    return [(o.choice.id, o.enabled) for o in options]


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.story = sample_story()
        self.state = engine.new_game(self.story)

    def test_new_game_starts_at_start_scene(self):
        self.assertEqual(self.state.scene_id, "arrival")
        self.assertEqual(self.state.turn, 0)

    def test_choice_moves_scene_and_advances_turn(self):
        result = engine.choose(self.story, self.state, "step_in")
        self.assertEqual(result.state.scene_id, "foyer")
        self.assertEqual(result.state.turn, 1)
        self.assertEqual(self.state.scene_id, "arrival", "original state must not change")

    def test_flags_hide_choices(self):
        state = engine.choose(self.story, self.state, "read_sign").state
        state = engine.choose(self.story, state, "back").state
        self.assertIn("read_sign", state.flags)
        self.assertNotIn("read_sign", [o.choice.id for o in engine.options_for(self.story, state)])

    def test_locked_choice_shown_disabled_then_unlocked_by_item(self):
        state = engine.choose(self.story, self.state, "step_in").state
        self.assertIn(("green_door", False), ids(engine.options_for(self.story, state)))
        with self.assertRaises(engine.ChoiceUnavailable):
            engine.choose(self.story, state, "green_door")

        result = engine.choose(self.story, state, "take_key")
        self.assertEqual(result.gained, ("brass_key",))
        options = ids(engine.options_for(self.story, result.state))
        self.assertIn(("green_door", True), options)
        self.assertNotIn("take_key", [cid for cid, _ in options])

        final = engine.choose(self.story, result.state, "green_door")
        self.assertEqual(final.lost, ("brass_key",))
        self.assertTrue(final.finished)

    def test_unknown_choice_rejected(self):
        with self.assertRaises(engine.ChoiceUnavailable):
            engine.choose(self.story, self.state, "fly_away")

    def test_state_round_trips_through_json(self):
        state = engine.GameState("foyer", turn=3, inventory=["brass_key"], flags={"read_sign"})
        self.assertEqual(engine.GameState.from_json(state.to_json()), state)


if __name__ == "__main__":
    unittest.main()
