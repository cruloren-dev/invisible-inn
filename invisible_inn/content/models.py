"""Plain data classes describing a story once it has been loaded from YAML.

These classes have no Discord or database dependencies, so the engine and the
content validator can use them freely (and they are easy to test).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Requirements:
    """Conditions a player must meet for a choice to be available.

    All listed conditions must be true (logical AND).
    """

    items: tuple[str, ...] = ()
    """Item ids the player must be carrying."""
    not_items: tuple[str, ...] = ()
    """Item ids the player must NOT be carrying."""
    flags: tuple[str, ...] = ()
    """Story flags that must be set."""
    not_flags: tuple[str, ...] = ()
    """Story flags that must NOT be set."""

    def is_empty(self) -> bool:
        return not (self.items or self.not_items or self.flags or self.not_flags)


@dataclass(frozen=True)
class Choice:
    id: str
    label: str
    goto: str
    description: str | None = None
    """Optional short hint shown under the option in dropdown menus."""
    requires: Requirements = field(default_factory=Requirements)
    show_locked: bool = False
    """If True, the choice is shown greyed-out when requirements aren't met
    (instead of being hidden)."""
    gives: tuple[str, ...] = ()
    takes: tuple[str, ...] = ()
    sets_flags: tuple[str, ...] = ()
    clears_flags: tuple[str, ...] = ()
    result_text: str | None = None
    """Optional line shown when this choice is picked (e.g. "The key is cold.")."""


@dataclass(frozen=True)
class Scene:
    id: str
    title: str
    text: str
    choices: tuple[Choice, ...] = ()
    ending: bool = False
    source_file: str = ""

    def choice(self, choice_id: str) -> Choice | None:
        for c in self.choices:
            if c.id == choice_id:
                return c
        return None


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    description: str = ""


@dataclass(frozen=True)
class Story:
    id: str
    title: str
    description: str
    start_scene: str
    scenes: dict[str, Scene]
    items: dict[str, Item]
    min_players: int = 1
    max_players: int = 1

    def scene(self, scene_id: str) -> Scene:
        return self.scenes[scene_id]

    def item_name(self, item_id: str) -> str:
        item = self.items.get(item_id)
        return item.name if item else item_id
