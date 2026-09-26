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
    content_dir = Path(argv[0]) if argv else Path("content/stories")
    report = load_all(content_dir)

    for story in report.stories.values():
        print(f"✔ {story.title} ({story.id}): {len(story.scenes)} scenes, {len(story.items)} items")
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
