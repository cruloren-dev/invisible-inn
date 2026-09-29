import tempfile
import unittest
from pathlib import Path

from invisible_inn.content import LoadReport, load_all, load_story

from .helpers import CONTENT_DIR, REAL_CONTENT_DIR, write_story


class SampleContentTests(unittest.TestCase):
    def test_sample_story_is_valid(self):
        report = load_all(CONTENT_DIR)
        self.assertEqual(report.errors, [])
        self.assertIn("invisible_inn", report.stories)

    def test_real_stories_are_valid(self):
        report = load_all(REAL_CONTENT_DIR)
        self.assertEqual(report.errors, [])
        self.assertTrue(report.stories)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, scenes, items="", start="start", story_extra=""):
        report = LoadReport()
        story = load_story(write_story(self.root, scenes, items, start, story_extra=story_extra), report)
        return story, report

    ROLES = """
        roles:
          scholar: {name: Scholar, description: Bookish.}
          mage: {name: Mage, playable: false}
    """

    def test_roles_and_role_content_load(self):
        story, report = self.load("""
            start:
              title: Start
              text: Shared text
              role_text:
                scholar: Scholar text
              choices:
                - {id: go, label: Go, goto: start}
                - {id: read, label: Read, goto: start, requires: {roles: [scholar]}}
        """, story_extra=self.ROLES)
        self.assertEqual(report.errors, [])
        self.assertEqual(list(story.roles), ["scholar", "mage"])
        self.assertFalse(story.roles["mage"].playable)
        scene = story.scene("start")
        self.assertEqual(scene.role_text, {"scholar": "Scholar text"})
        self.assertEqual(scene.choice("read").requires.roles, ("scholar",))

    def test_reports_unknown_roles(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              role_text:
                rogue: Sneaky text
              choices:
                - {id: go, label: Go, goto: start, requires: {roles: [bard]}}
        """, story_extra=self.ROLES)
        self.assertIsNone(story)
        joined = "\n".join(report.errors)
        self.assertIn("'rogue' is not a role", joined)
        self.assertIn("role 'bard' is not defined", joined)

    def test_role_result_text_loads_and_is_checked(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - id: go
                  label: Go
                  goto: start
                  result_text: Shared.
                  role_result_text: {scholar: Scholar's version}
        """, story_extra=self.ROLES)
        self.assertEqual(report.errors, [])
        self.assertEqual(story.scene("start").choice("go").role_result_text, {"scholar": "Scholar's version"})

    def test_reports_unknown_role_in_role_result_text(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: start, role_result_text: {bard: La la}}
        """, story_extra=self.ROLES)
        self.assertIsNone(story)
        self.assertIn("role_result_text: 'bard' is not a role", "\n".join(report.errors))

    def test_reports_unknown_role_in_not_roles(self):
        story, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: start, requires: {not_roles: [bard]}}
        """, story_extra=self.ROLES)
        self.assertIsNone(story)
        self.assertIn("role 'bard' is not defined", "\n".join(report.errors))

    def test_stuck_check_respects_not_roles(self):
        # Every choice is for someone else, so the Rogue has nothing here.
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: a, label: A, goto: end, requires: {not_roles: [rogue]}}
                - {id: b, label: B, goto: end, requires: {roles: [scholar]}}
            end: {title: End, text: Bye, ending: true}
        """, story_extra="""
            roles:
              scholar: {name: Scholar}
              rogue: {name: Rogue}
        """)
        self.assertIn("has no choices for the Rogue", "\n".join(report.warnings))
        self.assertNotIn("for the Scholar", "\n".join(report.warnings))

    def test_stuck_check_is_per_role(self):
        # The Scholar has a way on, but the Rogue's only choices need an item nobody can get.
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: read, label: Read, goto: end, requires: {roles: [scholar]}}
                - {id: pick, label: Pick, goto: end, requires: {roles: [rogue], items: [key]}}
            end: {title: End, text: Bye, ending: true}
        """, "key: {name: Key}\n", story_extra="""
            roles:
              scholar: {name: Scholar}
              rogue: {name: Rogue}
        """)
        stuck = [w for w in report.warnings if "stuck" in w]
        self.assertEqual(len(stuck), 1)
        self.assertIn("for the Rogue", stuck[0])

    def test_stuck_check_reports_a_role_with_no_choices(self):
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: read, label: Read, goto: end, requires: {roles: [scholar]}}
            end: {title: End, text: Bye, ending: true}
        """, story_extra="""
            roles:
              scholar: {name: Scholar}
              rogue: {name: Rogue}
        """)
        self.assertIn("has no choices for the Rogue", "\n".join(report.warnings))

    def test_role_only_choices_with_complementary_pairs_do_not_warn(self):
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: a, label: A, goto: end, requires: {roles: [rogue], items: [key]}}
                - {id: b, label: B, goto: end, requires: {roles: [rogue], not_items: [key]}}
                - {id: c, label: C, goto: end, requires: {roles: [scholar]}}
            end: {title: End, text: Bye, ending: true}
        """, "key: {name: Key}\n", story_extra="""
            roles:
              scholar: {name: Scholar}
              rogue: {name: Rogue}
        """)
        self.assertEqual([w for w in report.warnings if "stuck" in w or "no choices" in w], [])

    def test_reports_label_too_long_with_role_tag(self):
        label = "x" * 75  # fits alone, but not with "[Scholar] " in front
        story, report = self.load(f"""
            start:
              title: Start
              text: Hello
              choices:
                - {{id: go, label: Go, goto: start}}
                - {{id: read, label: {label}, goto: start, requires: {{roles: [scholar]}}}}
        """, story_extra=self.ROLES)
        self.assertIsNone(story)
        self.assertIn("with its role tag", "\n".join(report.errors))

    def write_quests(self, text):
        from textwrap import dedent
        (self.root / "test_story" / "quests.yaml").write_text(dedent(text))

    def test_quests_load_and_are_checked(self):
        write_story(self.root, """
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: start, starts_quests: [find], requires: {quests_done: [ghost]}}
        """, story_extra=self.ROLES)
        self.write_quests("""
            find: {title: Find it, description: Somewhere., role: scholar}
            lost: {title: Lost, role: bard}
            bad: {name: No title}
        """)
        report = LoadReport()
        story = load_story(self.root / "test_story", report)
        self.assertIsNone(story)
        joined = "\n".join(report.errors)
        self.assertIn("quest 'ghost' is not defined", joined)
        self.assertIn("role 'bard' is not defined", joined)
        self.assertIn("quests.yaml › bad: needs at least a 'title'", joined)

    def test_warns_about_quests_never_completed(self):
        write_story(self.root, """
            start:
              title: Start
              text: Hello
              choices:
                - {id: go, label: Go, goto: start, starts_quests: [find]}
        """)
        self.write_quests("""
            find: {title: Find it}
            unused: {title: Unused}
        """)
        report = LoadReport()
        story = load_story(self.root / "test_story", report)
        self.assertIsNotNone(story)
        self.assertEqual(story.quests["find"].title, "Find it")
        joined = "\n".join(report.warnings)
        self.assertIn("find: no choice completes this quest", joined)
        self.assertIn("unused: no choice starts or completes", joined)

    def test_complementary_choices_do_not_warn_about_getting_stuck(self):
        items = "key: {name: Key}\n"
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: a, label: A, goto: end, requires: {items: [key]}}
                - {id: b, label: B, goto: end, requires: {not_items: [key]}}
            end: {title: End, text: Bye, ending: true}
        """, items)
        self.assertEqual([w for w in report.warnings if "stuck" in w], [])

    def test_unmatched_conditions_still_warn_about_getting_stuck(self):
        _, report = self.load("""
            start:
              title: Start
              text: Hello
              choices:
                - {id: a, label: A, goto: end, requires: {items: [key]}}
                - {id: b, label: B, goto: end, requires: {flags: [f]}}
            end: {title: End, text: Bye, ending: true}
        """, "key: {name: Key}\n")
        self.assertTrue([w for w in report.warnings if "stuck" in w])

    def test_reports_no_playable_role(self):
        story, report = self.load("""
            start: {title: End, text: Bye, ending: true}
        """, story_extra="""
            roles:
              mage: {name: Mage, playable: false}
        """)
        self.assertIsNone(story)
        self.assertIn("at least one role must be playable", "\n".join(report.errors))

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
