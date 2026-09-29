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
        state = engine.GameState("foyer", turn=3, inventory=["brass_key"], flags={"read_sign"},
                                 roles=["scholar"])
        self.assertEqual(engine.GameState.from_json(state.to_json()), state)

    def test_old_saved_state_without_roles_still_loads(self):
        state = engine.GameState.from_json('{"scene_id": "foyer", "turn": 2}')
        self.assertEqual(state.roles, [])
        self.assertEqual(state.quests, {})

    def test_quest_state_round_trips_in_order(self):
        state = engine.GameState("foyer", quests={"b": engine.QUEST_COMPLETED, "a": engine.QUEST_ACTIVE})
        self.assertEqual(list(engine.GameState.from_json(state.to_json()).quests), ["b", "a"])


class QuestTests(unittest.TestCase):
    def setUp(self):
        self.story = sample_story()
        self.scholar = engine.new_game(self.story, ["scholar"])

    def play(self, state, *choices):
        result = None
        for choice_id in choices:
            result = engine.choose(self.story, state, choice_id)
            state = result.state
        return result

    def test_quest_is_hidden_until_started_then_completed(self):
        self.assertEqual(engine.visible_quests(self.story, self.scholar), ([], []))
        result = self.play(self.scholar, "step_in")
        self.assertEqual(result.quests_started, ("find_the_innkeeper",))
        active, done = engine.visible_quests(self.story, result.state)
        self.assertEqual(([q.id for q in active], done), (["find_the_innkeeper"], []))

        result = engine.choose(self.story, result.state, "ring_bell")
        self.assertEqual(result.quests_completed, ("find_the_innkeeper",))
        active, done = engine.visible_quests(self.story, result.state)
        self.assertEqual((active, [q.id for q in done]), ([], ["find_the_innkeeper"]))

    def test_starting_or_completing_twice_is_not_announced_again(self):
        state = self.play(self.scholar, "step_in", "ring_bell", "back_to_foyer").state
        again = engine.choose(self.story, state, "ring_bell")
        self.assertEqual((again.quests_started, again.quests_completed), ((), ()))
        self.assertEqual(again.state.quests["find_the_innkeeper"], engine.QUEST_COMPLETED)

    def test_secret_role_quest_flow(self):
        copied = self.play(self.scholar, "read_sign", "copy_cipher")
        self.assertEqual(copied.gained, ("cuff_cipher",))
        result = self.play(copied.state, "step_in", "ring_bell")
        self.assertIn("cuff_cipher", result.state.inventory, "kept until shown to the innkeeper")
        options = [o.choice.id for o in engine.options_for(self.story, result.state)]
        self.assertIn("ask_cipher", options, "needs the quest to be in progress")
        done = engine.choose(self.story, result.state, "ask_cipher")
        self.assertEqual(done.quests_completed, ("decode_the_sign",))
        self.assertEqual(done.lost, ("cuff_cipher",))
        self.assertNotIn("ask_cipher", [o.choice.id for o in engine.options_for(self.story, done.state)])

    def test_quest_requirement_blocks_choice(self):
        state = self.play(self.scholar, "step_in", "ring_bell").state
        with self.assertRaises(engine.ChoiceUnavailable):
            engine.choose(self.story, state, "ask_cipher")  # quest never started

    def test_role_quests_hidden_from_other_roles(self):
        state = engine.GameState("foyer", roles=["rogue"],
                                 quests={"decode_the_sign": engine.QUEST_ACTIVE,
                                         "find_the_innkeeper": engine.QUEST_ACTIVE})
        active, _ = engine.visible_quests(self.story, state)
        self.assertEqual([q.id for q in active], ["find_the_innkeeper"])


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.story = sample_story()
        self.sign = engine.GameState("sign")

    def test_story_needs_a_role_until_one_is_picked(self):
        state = engine.new_game(self.story)
        self.assertTrue(engine.needs_role(self.story, state))
        picked = engine.with_roles(state, ["scholar"])
        self.assertFalse(engine.needs_role(self.story, picked))
        self.assertEqual(state.roles, [], "original state must not change")

    def test_role_choice_only_for_that_role(self):
        self.assertNotIn("copy_cipher", [o.choice.id for o in engine.options_for(self.story, self.sign)])
        with self.assertRaises(engine.ChoiceUnavailable):
            engine.choose(self.story, self.sign, "copy_cipher")
        rogue = engine.with_roles(self.sign, ["rogue"])
        self.assertNotIn("copy_cipher", [o.choice.id for o in engine.options_for(self.story, rogue)])
        scholar = engine.with_roles(self.sign, ["scholar"])
        self.assertIn("copy_cipher", [o.choice.id for o in engine.options_for(self.story, scholar)])
        result = engine.choose(self.story, scholar, "copy_cipher")
        self.assertEqual(result.state.roles, ["scholar"], "roles carry over to the next scene")

    def test_role_text_replaces_shared_text(self):
        scene = self.story.scene("sign")
        scholar = engine.with_roles(self.sign, ["scholar"])
        rogue = engine.with_roles(self.sign, ["rogue"])
        self.assertIn("condensation cipher", engine.scene_text(scene, scholar))
        self.assertEqual(engine.scene_text(scene, rogue), scene.text)
        both = engine.with_roles(self.sign, ["scholar", "rogue"])
        self.assertEqual(engine.scene_text(scene, both), scene.text, "a mixed party gets the shared text")

    def test_not_roles_hides_a_choice_from_that_role_without_tagging_it(self):
        arrival = engine.GameState("arrival")
        def ids_for(roles):
            state = engine.with_roles(arrival, roles)
            return [o.choice.id for o in engine.options_for(self.story, state)]
        self.assertIn("leave", ids_for(["scholar"]))
        self.assertIn("leave", ids_for([]))
        self.assertNotIn("leave", ids_for(["mage"]))
        with self.assertRaises(engine.ChoiceUnavailable):
            engine.choose(self.story, engine.with_roles(arrival, ["mage"]), "leave")
        leave = self.story.scene("arrival").choice("leave")
        self.assertEqual(engine.choice_label(self.story, leave), "Walk away", "not_roles adds no tag")

    def test_greyed_out_choices_are_never_another_roles(self):
        # show_locked teases something the player can unlock. A choice for another role
        # can never be unlocked by this player, so it isn't shown at all.
        from invisible_inn.content.models import Choice, Requirements, Scene, Story
        scholars = Choice("read", "Read", "s", requires=Requirements(roles=("scholar",), flags=("saw_note",)),
                          show_locked=True)
        rogues = Choice("pick", "Pick", "s", requires=Requirements(roles=("rogue",), flags=("saw_note",)),
                        show_locked=True)
        not_rogue = Choice("wave", "Wave", "s", requires=Requirements(not_roles=("rogue",), flags=("saw_note",)),
                           show_locked=True)
        story = Story("t", "T", "", "s", {"s": Scene("s", "S", "t", (scholars, rogues, not_rogue))}, {})

        def shown(roles, flags=()):
            state = engine.GameState("s", roles=list(roles), flags=set(flags))
            return [(o.choice.id, o.enabled) for o in engine.options_for(story, state)]

        self.assertEqual(shown(["scholar"]), [("read", False), ("wave", False)],
                         "greyed out for the Scholar's own choice, but never the Rogue's")
        self.assertEqual(shown(["rogue"]), [("pick", False)])
        self.assertEqual(shown(["scholar"], ["saw_note"]), [("read", True), ("wave", True)])
        self.assertEqual(shown(["rogue"], ["saw_note"]), [("pick", True)])

    def test_role_result_text_replaces_shared_result_text(self):
        choice = self.story.scene("foyer").choice("take_key")
        base = "You lift the key from its hook. Nobody stops you."
        self.assertEqual(engine.result_text(choice, engine.GameState("foyer")), base)
        scholar = engine.GameState("foyer", roles=["scholar"])
        self.assertEqual(engine.result_text(choice, scholar), base, "no version for this role")
        rogue = engine.GameState("foyer", roles=["rogue"])
        self.assertIn("before anyone notices the hook", engine.result_text(choice, rogue))
        both = engine.GameState("foyer", roles=["rogue", "scholar"])
        self.assertEqual(engine.result_text(choice, both), base, "a mixed party gets the shared text")

    def test_role_choice_label_is_tagged(self):
        choice = self.story.scene("sign").choice("copy_cipher")
        self.assertEqual(engine.choice_label(self.story, choice), "[Scholar] Copy the cipher before it fades")
        plain = self.story.scene("sign").choice("back")
        self.assertEqual(engine.choice_label(self.story, plain), "Step back into the street")


if __name__ == "__main__":
    unittest.main()
