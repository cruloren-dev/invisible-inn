"""Plain data classes describing a story once it has been loaded from YAML.

These classes have no Discord or database dependencies, so the engine and the
content validator can use them freely (and they are easy to test).
"""

from __future__ import annotations

from dataclasses import dataclass, field


def role_label(label: str, role_names: list[str]) -> str:
    """A choice label with its role tag, e.g. "[Scholar] Examine the runes"."""
    return f"[{' / '.join(role_names)}] {label}" if role_names else label


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
    roles: tuple[str, ...] = ()
    """Role ids, any one of which must be in the party (e.g. only the Scholar)."""
    not_roles: tuple[str, ...] = ()
    """Role ids that must NOT be in the party. For choices about a character the
    player *is* (e.g. "Let Sable pick the lock", which the Rogue can't choose).
    Unlike ``roles``, this doesn't add a role tag to the button."""
    quests_active: tuple[str, ...] = ()
    """Quests that must be in progress (started, not yet completed)."""
    quests_done: tuple[str, ...] = ()
    """Quests that must be completed."""
    not_quests_done: tuple[str, ...] = ()
    """Quests that must NOT be completed."""

    def is_empty(self) -> bool:
        return not (self.items or self.not_items or self.flags or self.not_flags or self.roles
                    or self.not_roles or self.quests_active or self.quests_done or self.not_quests_done)

    def allows_role(self, role_id: str | None) -> bool:
        """Could a player of this role ever pass the role conditions? (Says nothing about
        items, flags or quests.)"""
        if self.roles and role_id not in self.roles:
            return False
        return role_id not in self.not_roles


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
    starts_quests: tuple[str, ...] = ()
    completes_quests: tuple[str, ...] = ()
    role_result_text: dict[str, str] = field(default_factory=dict)
    """Text to show instead of ``result_text`` when the party is a single role, keyed by role id."""


@dataclass(frozen=True)
class Scene:
    id: str
    title: str
    text: str
    choices: tuple[Choice, ...] = ()
    ending: bool = False
    source_file: str = ""
    role_text: dict[str, str] = field(default_factory=dict)
    """Text to show instead of ``text`` when the party is a single role, keyed by role id."""

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
class Quest:
    id: str
    title: str
    description: str = ""
    role: str | None = None
    """If set, a secret quest that belongs to this role. Otherwise shared by the party."""


@dataclass(frozen=True)
class Role:
    id: str
    name: str
    """Short name, used in choice labels, e.g. "[Scholar] Examine the runes"."""
    description: str = ""
    playable: bool = True
    """False shows the role as "coming soon" in the role picker."""


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
    roles: dict[str, Role] = field(default_factory=dict)
    """Characters players choose between. Empty means the story has no role choice."""
    quests: dict[str, Quest] = field(default_factory=dict)

    def scene(self, scene_id: str) -> Scene:
        return self.scenes[scene_id]

    def role_name(self, role_id: str) -> str:
        role = self.roles.get(role_id)
        return role.name if role else role_id

    def quest_title(self, quest_id: str) -> str:
        quest = self.quests.get(quest_id)
        return quest.title if quest else quest_id

    def item_name(self, item_id: str) -> str:
        item = self.items.get(item_id)
        return item.name if item else item_id
