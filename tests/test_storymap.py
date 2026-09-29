import unittest

from invisible_inn.content import load_all
from invisible_inn.content.storymap import build, describe_effects, describe_requirements, diagram

from .helpers import CONTENT_DIR, REAL_CONTENT_DIR


class StoryMapTests(unittest.TestCase):
    def setUp(self):
        self.story = load_all(CONTENT_DIR).stories["invisible_inn"]

    def test_diagram_has_every_scene_and_marks_start_and_endings(self):
        text = diagram(self.story)
        self.assertTrue(text.startswith("```mermaid\nflowchart TD"))
        for scene_id in self.story.scenes:
            self.assertIn(f"s_{scene_id}", text)
        self.assertIn("class s_arrival start", text)
        self.assertIn("s_ending_walk_away", text.split("class ")[-2])

    def test_locked_paths_are_dotted_and_one_time_choices_are_not(self):
        text = diagram(self.story)
        self.assertIn('s_foyer -.->|"🔒 Open the green door"| s_green_room', text)
        # Reading the sign only disappears once it's been read: not a lock.
        self.assertIn('s_arrival -->|"Look closer at the blank sign"| s_sign', text)

    def test_each_role_gets_only_the_scenes_and_choices_it_can_reach(self):
        from invisible_inn.content.models import Choice, Requirements, Role, Scene, Story
        scenes = {
            "start": Scene("start", "Start", "t", (
                Choice("shared", "Shared", "hall", requires=Requirements(not_roles=("scholar",))),
                Choice("study", "Study", "archive", requires=Requirements(roles=("scholar",))),
            )),
            "hall": Scene("hall", "Hall", "t", ending=True),
            "archive": Scene("archive", "Archive", "t", ending=True),
        }
        roles = {"scholar": Role("scholar", "Scholar"), "rogue": Role("rogue", "Rogue")}
        story = Story("t", "T", "", "start", scenes, {}, roles=roles)
        self.assertIn("s_archive", diagram(story, "scholar"))
        self.assertNotIn("s_hall", diagram(story, "scholar"), "not_roles: hidden from the Scholar")
        self.assertNotIn("s_archive", diagram(story, "rogue"))
        self.assertIn("s_hall", diagram(story, "rogue"))
        self.assertIn("s_archive", diagram(story), "no role: everything")

    def test_map_has_a_diagram_per_playable_role(self):
        text, _ = build(CONTENT_DIR)
        self.assertIn("### Scholar's path", text)
        self.assertIn("### Rogue's path", text)
        self.assertNotIn("Mage's path", text, "the Mage isn't playable yet")
        self.assertEqual(text.count("```mermaid"), 2)

    def test_plain_return_trips_have_no_label(self):
        self.assertIn("s_innkeeper --> s_foyer\n", diagram(self.story) + "\n")

    def test_tables_describe_needs_and_effects(self):
        green = self.story.scene("foyer").choice("green_door")
        self.assertEqual(describe_requirements(self.story, green), "has Brass Key (greyed out until then)")
        self.assertEqual(describe_effects(self.story, green), "➖ Brass Key")
        cipher = self.story.scene("sign").choice("copy_cipher")
        self.assertIn("Scholar only", describe_requirements(self.story, cipher))
        self.assertIn("📜 starts *The Vanishing Letters*", describe_effects(self.story, cipher))

    def test_real_story_map_builds(self):
        text, errors = build(REAL_CONTENT_DIR)
        self.assertEqual(errors, [])
        self.assertIn("```mermaid", text)
        self.assertIn("## Scenes in detail", text)


if __name__ == "__main__":
    unittest.main()
