"""Generate a story map for writers: a diagram of every scene and path, plus a
table of each scene's choices, what they need and what they do.

Usage (from the repository root)::

    python -m invisible_inn.content.storymap                  # prints the map
    python -m invisible_inn.content.storymap --out docs/story-map.md

The diagram uses Mermaid, which GitHub draws automatically when it shows a
Markdown file. A GitHub Action regenerates ``docs/story-map.md`` whenever story
content changes on ``main``, so the map never needs editing by hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .loader import load_all
from .models import Choice, Requirements, Story

MAX_EDGE_LABEL = 40


def _mermaid_text(text: str) -> str:
    return text.replace('"', "#quot;").replace("\n", " ").strip()


def _cell(text: str) -> str:
    """Text safe to put in a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _node(scene_id: str) -> str:
    # Prefix ids: words like "end" are reserved in Mermaid.
    return f"s_{scene_id}"


def _label(story: Story, choice: Choice) -> str:
    roles = [story.role_name(r) for r in choice.requires.roles]
    return (f"[{' / '.join(roles)}] " if roles else "") + choice.label


def _is_locked(req: Requirements) -> bool:
    """Needs something the player has to get first (an item, flag or quest progress).

    "Must NOT have" conditions are left out: at the start they're always met, and they
    usually just make a choice disappear once it's been used (e.g. a one-time pick-up).
    """
    return bool(req.items or req.flags or req.quests_active or req.quests_done)


def _is_limited(req: Requirements) -> bool:
    """Can disappear later (a one-time choice)."""
    return bool(req.not_items or req.not_flags or req.not_quests_done)


def describe_requirements(story: Story, choice: Choice) -> str:
    r = choice.requires
    parts = []
    parts += [f"{story.role_name(x)} only" for x in r.roles]
    parts += [f"has {story.item_name(x)}" for x in r.items]
    parts += [f"doesn't have {story.item_name(x)}" for x in r.not_items]
    parts += [f"flag `{x}`" for x in r.flags]
    parts += [f"not flag `{x}`" for x in r.not_flags]
    parts += [f"quest *{story.quest_title(x)}* in progress" for x in r.quests_active]
    parts += [f"quest *{story.quest_title(x)}* done" for x in r.quests_done]
    parts += [f"quest *{story.quest_title(x)}* not done" for x in r.not_quests_done]
    if not parts:
        return "—"
    note = ""
    if _is_locked(r):
        note = " (greyed out until then)" if choice.show_locked else " (hidden until then)"
    elif _is_limited(r):
        note = " (disappears once that changes)"
    return "; ".join(parts) + note


def describe_effects(story: Story, choice: Choice) -> str:
    parts = []
    parts += [f"➕ {story.item_name(x)}" for x in choice.gives]
    parts += [f"➖ {story.item_name(x)}" for x in choice.takes]
    parts += [f"sets `{x}`" for x in choice.sets_flags]
    parts += [f"clears `{x}`" for x in choice.clears_flags]
    parts += [f"📜 starts *{story.quest_title(x)}*" for x in choice.starts_quests]
    parts += [f"✅ completes *{story.quest_title(x)}*" for x in choice.completes_quests]
    return "; ".join(parts) or "—"


def _depths(story: Story) -> dict[str, int]:
    """How many steps each scene is from the start (breadth-first)."""
    depth = {story.start_scene: 0}
    queue = [story.start_scene]
    while queue:
        scene_id = queue.pop(0)
        for c in story.scenes[scene_id].choices:
            if c.goto not in depth:
                depth[c.goto] = depth[scene_id] + 1
                queue.append(c.goto)
    return depth


def diagram(story: Story) -> str:
    lines = ["```mermaid", "flowchart TD"]
    for scene in story.scenes.values():
        stays = [c for c in scene.choices if c.goto == scene.id]
        label = _mermaid_text(scene.title)
        if stays:
            label += f"<br/><small>↺ {len(stays)} action{'s' if len(stays) != 1 else ''} here</small>"
        if scene.ending:
            shape = f'(["{label}"])'
        elif scene.id == story.start_scene:
            shape = f'[/"{label}"/]'
        else:
            shape = f'["{label}"]'
        lines.append(f"    {_node(scene.id)}{shape}")
    # Plain arrows back to earlier scenes ("Back to the main hall") are drawn without
    # labels, which keeps the diagram readable; the tables list them in full.
    depth = _depths(story)
    edges: dict[tuple[str, str], list[Choice]] = {}
    for scene in story.scenes.values():
        for c in scene.choices:
            if c.goto != scene.id:
                edges.setdefault((scene.id, c.goto), []).append(c)
    for (src, dst), choices in edges.items():
        locked = all(_is_locked(c.requires) for c in choices)
        backwards = depth.get(dst, 0) < depth.get(src, 0)
        does_something = any(describe_effects(story, c) != "—" for c in choices)
        if backwards and not locked and not does_something:
            lines.append(f"    {_node(src)} --> {_node(dst)}")
            continue
        text = " / ".join(_short(_label(story, c), MAX_EDGE_LABEL) for c in choices)
        text = ("🔒 " if locked else "") + text
        arrow = "-.->" if locked else "-->"
        lines.append(f'    {_node(src)} {arrow}|"{_mermaid_text(text)}"| {_node(dst)}')
    endings = [_node(s.id) for s in story.scenes.values() if s.ending]
    lines.append("    classDef ending fill:#3E7C59,color:#fff,stroke:#2b5a40")
    lines.append("    classDef start fill:#6B4E9B,color:#fff,stroke:#4d3870")
    if endings:
        lines.append(f"    class {','.join(endings)} ending")
    lines.append(f"    class {_node(story.start_scene)} start")
    lines.append("```")
    return "\n".join(lines)


def scene_tables(story: Story) -> str:
    out = []
    for scene in story.scenes.values():
        kind = " · **ending**" if scene.ending else (" · **start**" if scene.id == story.start_scene else "")
        out.append(f"### {scene.title}\n")
        extras = f" · own text for: {', '.join(story.role_name(r) for r in scene.role_text)}" if scene.role_text else ""
        out.append(f"`{scene.id}` in `scenes/{scene.source_file}`{kind}{extras}\n")
        if not scene.choices:
            out.append("")
            continue
        out.append("| Choice | Leads to | Needs | Does |")
        out.append("|---|---|---|---|")
        for c in scene.choices:
            target = "*(stays here)*" if c.goto == scene.id else f"{story.scene(c.goto).title} (`{c.goto}`)"
            out.append(f"| {_cell(_label(story, c))} | {_cell(target)} | {_cell(describe_requirements(story, c))}"
                       f" | {_cell(describe_effects(story, c))} |")
        out.append("")
    return "\n".join(out)


def story_map(story: Story, warnings: list[str]) -> str:
    roles = ", ".join(
        r.name + ("" if r.playable else " (coming soon)") for r in story.roles.values()
    ) or "none"
    parts = [
        f"## {story.title}",
        "",
        f"{len(story.scenes)} scenes · {len(story.items)} items · {len(story.quests)} quests · roles: {roles}",
        "",
        "**How to read the diagram:** the slanted box is where the story starts, and rounded green boxes are "
        "endings. **Dotted arrows with 🔒** need something first (an item, flag or quest); solid arrows don't, "
        "though some disappear after they've been used once. \"[Scholar]\" marks a choice for one role. "
        "\"↺ N actions here\" counts choices that stay in the same scene. Arrow labels are shortened; the "
        "tables below have the full text and every condition.",
        "",
        diagram(story),
        "",
    ]
    mine = [w for w in warnings if story.id in w or any(s.source_file in w for s in story.scenes.values())]
    if mine:
        parts += ["### Checker warnings", ""] + [f"- ⚠ {_cell(w)}" for w in mine] + [""]
    parts += ["## Scenes in detail", "", scene_tables(story)]
    return "\n".join(parts)


def build(content_dir: Path) -> tuple[str, list[str]]:
    report = load_all(content_dir)
    header = (
        "# Story map\n\n"
        "> **Generated automatically from the story files. Don't edit this page by hand:** it is\n"
        "> rebuilt whenever story changes are merged into `main`. To change the story, edit the\n"
        "> files in `content/stories/` (see `docs/editing-guide.md`).\n"
    )
    body = [story_map(s, report.warnings) for s in report.stories.values()]
    return header + "\n" + "\n\n".join(body), report.errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        del args[i:i + 2]
    content_dir = Path(args[0]) if args else Path("content/stories")
    text, errors = build(content_dir)
    if errors:
        print("The story has errors, so no map was made. Run the validator to see them:", file=sys.stderr)
        print("    python -m invisible_inn.content.validate", file=sys.stderr)
        return 1
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # emoji on Windows consoles
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
