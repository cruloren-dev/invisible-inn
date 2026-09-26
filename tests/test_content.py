import tempfile
import unittest
from pathlib import Path

from invisible_inn.content import LoadReport, load_all, load_story

from .helpers import CONTENT_DIR, write_story


class SampleContentTests(unittest.TestCase):
    def test_bundled_stories_are_valid(self):
        report = load_all(CONTENT_DIR)
        self.assertEqual(report.errors, [])
        self.assertIn("invisible_inn", report.stories)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, scenes, items="", start="start"):
        report = LoadReport()
        story = load_story(write_story(self.root, scenes, items, start), report)
        return story, report

    def test_minimal_story_loads(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: end}
            end:
              title: End
              text: Bye
              ending: true
        """)
        self.assertIsNotNone(story)
        self.assertEqual(report.errors, [])
        self.assertEqual(story.scene("start").choices[0].goto, "end")

    def test_reports_missing_goto_and_item(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: nowhere, gives: [ghost_item]}
        """)
        self.assertIsNone(story)
        joined = "\n".join(report.errors)
        self.assertIn("goto 'nowhere'", joined)
        self.assertIn("item 'ghost_item'", joined)

    def test_reports_bad_start_scene(self):
        story, report = self.load("""
            end: {title: End, text: Bye, ending: true}
        """, start="missing")
        self.assertIsNone(story)
        self.assertTrue(any("start_scene" in e for e in report.errors))

    def test_reports_bad_ids_and_long_labels(self):
        story, report = self.load(f"""
            start:
              title: Start
              text: Hello
              choices:
                - {{id: "Bad Id", label: Go, goto: start}}
                - {{id: ok, label: "{'x' * 90}", goto: start}}
        """)
        joined = "\n".join(report.errors)
        self.assertIn("'id' must be", joined)
        self.assertIn("Discord allows 80", joined)

    def test_reports_unknown_keys(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              ending: true
              colour: red
        """)
        self.assertTrue(any("unknown key 'colour'" in e for e in report.errors))

    def test_non_ending_scene_needs_choices(self):
        story, report = self.load("""
            start: {title: Start, text: Hello}
        """)
        self.assertTrue(any("has no choices" in e for e in report.errors))

    def test_warns_about_unreachable_scene(self):
        story, report = self.load("""
            start: {title: Start, text: Hi, ending: true}
            lonely: {title: Lonely, text: Nobody comes here, ending: true}
        """)
        self.assertIsNotNone(story)
        self.assertTrue(any("lonely" in w and "unreachable" in w for w in report.warnings))


if __name__ == "__main__":
    unittest.main()
