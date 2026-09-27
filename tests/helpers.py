from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parent.parent
# Tests play the sample story in tests/fixtures, which shows every content feature,
# so writers can change the real story in content/stories freely.
CONTENT_DIR = REPO_ROOT / "tests" / "fixtures" / "stories"
REAL_CONTENT_DIR = REPO_ROOT / "content" / "stories"


def write_story(root: Path, scenes_yaml: str, items_yaml: str = "", start: str = "start",
                story_id: str = "test_story", story_extra: str = "") -> Path:
    """Create a minimal story folder for tests and return its path.

    ``story_extra`` is appended to story.yaml (e.g. a ``roles:`` block).
    """
    story_dir = root / story_id
    (story_dir / "scenes").mkdir(parents=True)
    (story_dir / "story.yaml").write_text(f"title: Test\nstart_scene: {start}\n" + dedent(story_extra))
    if items_yaml:
        (story_dir / "items.yaml").write_text(dedent(items_yaml))
    (story_dir / "scenes" / "main.yaml").write_text(dedent(scenes_yaml))
    return story_dir
