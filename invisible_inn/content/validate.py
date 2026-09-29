"""Check story content for mistakes without starting the bot.

Usage::

    python -m invisible_inn.content.validate            # checks ./content/stories
    python -m invisible_inn.content.validate path/to/stories

Exits with status 1 if there are errors (warnings alone don't fail).
"""

from __future__ import annotations

import sys
from pathlib import Path

from .loader import load_all


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # ✔ and ⚠ on older Windows consoles
    except (AttributeError, ValueError):
        pass  # not a real console (e.g. captured by a test): leave it alone
    content_dir = Path(argv[0]) if argv else Path("content/stories")
    report = load_all(content_dir)

    for story in report.stories.values():
        roles = f", roles: {', '.join(r.name for r in story.roles.values())}" if story.roles else ""
        print(f"✔ {story.title} ({story.id}): {len(story.scenes)} scenes, {len(story.items)} items, "
              f"{len(story.quests)} quests{roles}")
    for w in report.warnings:
        print(f"⚠ warning: {w}")
    for e in report.errors:
        print(f"✘ error: {e}")

    if report.errors:
        print(f"\n{len(report.errors)} error(s) found.")
        return 1
    print("\nContent looks good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
