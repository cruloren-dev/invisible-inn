"""Load story content from YAML files and check it for mistakes.

Directory layout for one story::

    content/stories/<story_id>/
        story.yaml          # title, description, start_scene, player counts
        items.yaml          # optional: every item in the story
        scenes/*.yaml       # one or more files, each a mapping of scene_id -> scene

The loader collects *every* problem it finds (rather than stopping at the first)
so writers can fix a batch of mistakes in one go.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import Choice, Item, Requirements, Scene, Story

# Discord limits we must respect when rendering content.
MAX_TITLE = 256          # embed title
MAX_TEXT = 4000          # embed description is 4096; leave room for extras
MAX_LABEL = 80           # button label
MAX_OPTION_DESC = 100    # select-menu option description
MAX_CHOICES = 25         # select-menu option limit

ID_PATTERN = re.compile(r"^[a-z0-9_]{1,32}$")


class ContentError(Exception):
    """Raised when story content is invalid. ``errors`` lists every problem."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass
class LoadReport:
    stories: dict[str, Story] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _tuple_of_str(value: Any, where: str, errors: list[str]) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return tuple(value)
    errors.append(f"{where}: expected a name or a list of names, got {value!r}")
    return ()


def _read_yaml(path: Path, errors: list[str]) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        errors.append(f"{path}: not valid YAML ({exc})")
    except OSError as exc:
        errors.append(f"{path}: could not be read ({exc})")
    return None


def _parse_requirements(raw: Any, where: str, errors: list[str]) -> Requirements:
    if raw is None:
        return Requirements()
    if not isinstance(raw, dict):
        errors.append(f"{where}.requires: expected a mapping")
        return Requirements()
    allowed = {"items", "not_items", "flags", "not_flags"}
    for key in raw:
        if key not in allowed:
            errors.append(f"{where}.requires: unknown key '{key}' (allowed: {', '.join(sorted(allowed))})")
    return Requirements(
        items=_tuple_of_str(raw.get("items"), f"{where}.requires.items", errors),
        not_items=_tuple_of_str(raw.get("not_items"), f"{where}.requires.not_items", errors),
        flags=_tuple_of_str(raw.get("flags"), f"{where}.requires.flags", errors),
        not_flags=_tuple_of_str(raw.get("not_flags"), f"{where}.requires.not_flags", errors),
    )


CHOICE_KEYS = {
    "id", "label", "goto", "description", "requires", "show_locked",
    "gives", "takes", "sets_flags", "clears_flags", "result_text",
}
SCENE_KEYS = {"title", "text", "choices", "ending"}


def _parse_choice(raw: Any, where: str, errors: list[str]) -> Choice | None:
    if not isinstance(raw, dict):
        errors.append(f"{where}: each choice must be a mapping")
        return None
    for key in raw:
        if key not in CHOICE_KEYS:
            errors.append(f"{where}: unknown key '{key}'")
    cid, label, goto = raw.get("id"), raw.get("label"), raw.get("goto")
    ok = True
    if not isinstance(cid, str) or not ID_PATTERN.match(cid):
        errors.append(f"{where}: 'id' must be 1-32 characters of a-z, 0-9 or _ (got {cid!r})")
        ok = False
    if not isinstance(label, str) or not label.strip():
        errors.append(f"{where}: 'label' is required")
        ok = False
    elif len(label) > MAX_LABEL:
        errors.append(f"{where}: 'label' is {len(label)} characters; Discord allows {MAX_LABEL}")
    if not isinstance(goto, str):
        errors.append(f"{where}: 'goto' (the scene this choice leads to) is required")
        ok = False
    desc = raw.get("description")
    if desc is not None and (not isinstance(desc, str) or len(desc) > MAX_OPTION_DESC):
        errors.append(f"{where}: 'description' must be text of at most {MAX_OPTION_DESC} characters")
    if not ok:
        return None
    return Choice(
        id=cid,
        label=label.strip(),
        goto=goto,
        description=desc if isinstance(desc, str) else None,
        requires=_parse_requirements(raw.get("requires"), where, errors),
        show_locked=bool(raw.get("show_locked", False)),
        gives=_tuple_of_str(raw.get("gives"), f"{where}.gives", errors),
        takes=_tuple_of_str(raw.get("takes"), f"{where}.takes", errors),
        sets_flags=_tuple_of_str(raw.get("sets_flags"), f"{where}.sets_flags", errors),
        clears_flags=_tuple_of_str(raw.get("clears_flags"), f"{where}.clears_flags", errors),
        result_text=raw.get("result_text"),
    )


def _parse_scene(scene_id: str, raw: Any, path: Path, errors: list[str]) -> Scene | None:
    where = f"{path.name} › {scene_id}"
    if not ID_PATTERN.match(str(scene_id)):
        errors.append(f"{where}: scene ids must be 1-32 characters of a-z, 0-9 or _")
        return None
    if not isinstance(raw, dict):
        errors.append(f"{where}: a scene must be a mapping with title, text and choices")
        return None
    for key in raw:
        if key not in SCENE_KEYS:
            errors.append(f"{where}: unknown key '{key}'")
    title, text = raw.get("title"), raw.get("text")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{where}: 'title' is required")
        return None
    if len(title) > MAX_TITLE:
        errors.append(f"{where}: 'title' is longer than {MAX_TITLE} characters")
    if not isinstance(text, str) or not text.strip():
        errors.append(f"{where}: 'text' is required")
        return None
    if len(text) > MAX_TEXT:
        errors.append(f"{where}: 'text' is {len(text)} characters; the limit is {MAX_TEXT}. Split it into two scenes.")

    ending = bool(raw.get("ending", False))
    raw_choices = raw.get("choices") or []
    if not isinstance(raw_choices, list):
        errors.append(f"{where}: 'choices' must be a list")
        raw_choices = []
    choices = []
    for i, rc in enumerate(raw_choices, start=1):
        c = _parse_choice(rc, f"{where} › choice {i}", errors)
        if c:
            choices.append(c)

    ids = [c.id for c in choices]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"{where}: two choices share the id '{dup}'")
    if len(choices) > MAX_CHOICES:
        errors.append(f"{where}: {len(choices)} choices; Discord menus allow at most {MAX_CHOICES}")
    if ending and choices:
        errors.append(f"{where}: an ending scene cannot have choices")
    if not ending and not choices and not raw_choices:
        errors.append(f"{where}: has no choices — add some, or mark it 'ending: true'")

    return Scene(
        id=scene_id, title=title.strip(), text=text.rstrip(), choices=tuple(choices),
        ending=ending, source_file=path.name,
    )


def load_story(story_dir: Path, report: LoadReport | None = None) -> Story | None:
    """Load one story directory. Problems are added to ``report``."""
    report = report if report is not None else LoadReport()
    errors: list[str] = []
    story_dir = Path(story_dir)

    meta = _read_yaml(story_dir / "story.yaml", errors)
    if not isinstance(meta, dict):
        if not errors:
            errors.append(f"{story_dir / 'story.yaml'}: must be a mapping with title and start_scene")
        report.errors.extend(errors)
        return None

    story_id = story_dir.name
    if not ID_PATTERN.match(story_id):
        errors.append(f"{story_dir}: folder name must be 1-32 characters of a-z, 0-9 or _")

    # Items
    items: dict[str, Item] = {}
    items_path = story_dir / "items.yaml"
    if items_path.exists():
        raw_items = _read_yaml(items_path, errors) or {}
        if not isinstance(raw_items, dict):
            errors.append(f"{items_path}: must be a mapping of item_id -> item")
            raw_items = {}
        for item_id, raw in raw_items.items():
            if not ID_PATTERN.match(str(item_id)):
                errors.append(f"items.yaml › {item_id}: item ids must be 1-32 characters of a-z, 0-9 or _")
                continue
            if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
                errors.append(f"items.yaml › {item_id}: needs at least a 'name'")
                continue
            items[item_id] = Item(id=item_id, name=raw["name"], description=raw.get("description", "") or "")

    # Scenes
    scenes: dict[str, Scene] = {}
    scene_files = sorted((story_dir / "scenes").glob("*.yaml")) + sorted((story_dir / "scenes").glob("*.yml"))
    if not scene_files:
        errors.append(f"{story_dir / 'scenes'}: no scene files found")
    for path in scene_files:
        raw_scenes = _read_yaml(path, errors)
        if raw_scenes is None:
            continue
        if not isinstance(raw_scenes, dict):
            errors.append(f"{path.name}: must be a mapping of scene_id -> scene")
            continue
        for scene_id, raw in raw_scenes.items():
            scene_id = str(scene_id)
            if scene_id in scenes:
                errors.append(
                    f"{path.name} › {scene_id}: scene id already used in {scenes[scene_id].source_file}"
                )
                continue
            scene = _parse_scene(scene_id, raw, path, errors)
            if scene:
                scenes[scene_id] = scene

    start = meta.get("start_scene")
    if not isinstance(start, str) or start not in scenes:
        errors.append(f"story.yaml: start_scene '{start}' is not a scene that exists")

    min_p, max_p = meta.get("min_players", 1), meta.get("max_players", 1)
    if not (isinstance(min_p, int) and isinstance(max_p, int) and 1 <= min_p <= max_p <= 10):
        errors.append("story.yaml: min_players/max_players must be whole numbers with 1 ≤ min ≤ max ≤ 10")
        min_p, max_p = 1, 1

    # Cross-references: goto targets, items, flags
    set_flags: set[str] = set()
    for scene in scenes.values():
        for c in scene.choices:
            set_flags.update(c.sets_flags)
    for scene in scenes.values():
        for c in scene.choices:
            where = f"{scene.source_file} › {scene.id} › {c.id}"
            if c.goto not in scenes:
                errors.append(f"{where}: goto '{c.goto}' is not a scene that exists")
            for item_id in (*c.gives, *c.takes, *c.requires.items, *c.requires.not_items):
                if item_id not in items:
                    errors.append(f"{where}: item '{item_id}' is not defined in items.yaml")
            for flag in (*c.requires.flags, *c.requires.not_flags):
                if flag not in set_flags:
                    report.warnings.append(f"{where}: checks flag '{flag}', but no choice ever sets it")

    if errors:
        report.errors.extend(errors)
        return None

    story = Story(
        id=story_id,
        title=str(meta.get("title") or story_id),
        description=str(meta.get("description") or ""),
        start_scene=start,
        scenes=scenes,
        items=items,
        min_players=min_p,
        max_players=max_p,
    )
    report.warnings.extend(_reachability_warnings(story))
    return story


def _reachability_warnings(story: Story) -> list[str]:
    warnings = []
    seen = {story.start_scene}
    queue = deque([story.start_scene])
    while queue:
        for c in story.scenes[queue.popleft()].choices:
            if c.goto not in seen:
                seen.add(c.goto)
                queue.append(c.goto)
    for scene_id, scene in story.scenes.items():
        if scene_id not in seen:
            warnings.append(f"{scene.source_file} › {scene_id}: no choice leads here (unreachable)")
    if not any(s.ending for s in story.scenes.values()):
        warnings.append(f"{story.id}: has no ending scene")
    for scene in story.scenes.values():
        if scene.choices and all(not c.requires.is_empty() for c in scene.choices):
            warnings.append(
                f"{scene.source_file} › {scene.id}: every choice has requirements — "
                "players could get stuck here"
            )
    return warnings


def load_all(content_dir: Path) -> LoadReport:
    """Load every story under ``content_dir``."""
    report = LoadReport()
    content_dir = Path(content_dir)
    if not content_dir.is_dir():
        report.errors.append(f"{content_dir}: content folder not found")
        return report
    for story_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
        story = load_story(story_dir, report)
        if story:
            report.stories[story.id] = story
    if not report.stories and not report.errors:
        report.errors.append(f"{content_dir}: no stories found")
    return report
