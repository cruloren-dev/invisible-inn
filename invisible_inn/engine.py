"""Game rules: what a player can do in a scene and what happens when they do it.

The engine is pure Python — no Discord, no database — so it is easy to test
and reuse (e.g. for group play later).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .content.models import Choice, Quest, Requirements, Scene, Story, role_label


class ChoiceUnavailable(Exception):
    """The requested choice doesn't exist in this scene or its requirements aren't met."""


@dataclass
class GameState:
    scene_id: str
    turn: int = 0
    """Increments on every choice. Buttons carry the turn they were made for,
    so clicks on old messages (or double-clicks) are ignored."""
    inventory: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    roles: list[str] = field(default_factory=list)
    """Roles in the party. Solo games have one. Empty until the player picks a role
    (or always empty, for stories without roles)."""
    quests: dict[str, str] = field(default_factory=dict)
    """Quest id -> ACTIVE or COMPLETED, in the order they were discovered.
    Quests the story hasn't introduced yet aren't here."""

    def to_json(self) -> str:
        return json.dumps({
            "scene_id": self.scene_id,
            "turn": self.turn,
            "inventory": self.inventory,
            "flags": sorted(self.flags),
            "roles": self.roles,
            "quests": self.quests,
        })

    @classmethod
    def from_json(cls, raw: str) -> "GameState":
        data = json.loads(raw)
        return cls(
            scene_id=data["scene_id"],
            turn=int(data.get("turn", 0)),
            inventory=list(data.get("inventory", [])),
            flags=set(data.get("flags", [])),
            roles=list(data.get("roles", [])),
            quests=dict(data.get("quests", {})),
        )


QUEST_ACTIVE, QUEST_COMPLETED = "active", "completed"


@dataclass(frozen=True)
class ChoiceOption:
    choice: Choice
    enabled: bool


@dataclass(frozen=True)
class ChoiceResult:
    state: GameState
    scene: Scene
    chosen: Choice
    gained: tuple[str, ...]
    lost: tuple[str, ...]
    quests_started: tuple[str, ...] = ()
    quests_completed: tuple[str, ...] = ()

    @property
    def finished(self) -> bool:
        return self.scene.ending


def new_game(story: Story, roles: list[str] | tuple[str, ...] = ()) -> GameState:
    return GameState(scene_id=story.start_scene, roles=list(roles))


def needs_role(story: Story, state: GameState) -> bool:
    """True if the story has roles and the player hasn't picked one yet."""
    return bool(story.roles) and not state.roles


def with_roles(state: GameState, roles: list[str]) -> GameState:
    """A copy of ``state`` with the party's roles set."""
    return GameState(scene_id=state.scene_id, turn=state.turn, inventory=list(state.inventory),
                     flags=set(state.flags), roles=list(roles), quests=dict(state.quests))


def meets(req: Requirements, state: GameState) -> bool:
    inv = set(state.inventory)
    return (
        all(i in inv for i in req.items)
        and not any(i in inv for i in req.not_items)
        and all(f in state.flags for f in req.flags)
        and not any(f in state.flags for f in req.not_flags)
        and (not req.roles or any(r in state.roles for r in req.roles))
        and all(state.quests.get(q) == QUEST_ACTIVE for q in req.quests_active)
        and all(state.quests.get(q) == QUEST_COMPLETED for q in req.quests_done)
        and not any(state.quests.get(q) == QUEST_COMPLETED for q in req.not_quests_done)
    )


def quest_visible(story: Story, state: GameState, quest_id: str) -> bool:
    """Shared quests are visible to everyone; a secret quest only to a party with its role.

    The story can still start and complete another role's secret quest (e.g. the
    Rogue's, while the Rogue is a background character); the Scholar just never
    sees it, in /quests or in scene announcements.
    """
    quest = story.quests.get(quest_id)
    return quest is not None and (not quest.role or quest.role in state.roles)


def visible_quests(story: Story, state: GameState) -> tuple[list[Quest], list[Quest]]:
    """(active, completed) quests this party can see, in the order they were discovered.

    A role's secret quests are only listed for a party with that role. (For group
    play, this will need to filter by the player asking instead.)
    """
    active, completed = [], []
    for quest_id, status in state.quests.items():
        quest = story.quests.get(quest_id)
        if quest is None or not quest_visible(story, state, quest_id):
            continue
        (completed if status == QUEST_COMPLETED else active).append(quest)
    return active, completed


def scene_text(scene: Scene, state: GameState) -> str:
    """The scene's text for this party: a role's own version if there's one role, else the shared text."""
    if len(state.roles) == 1:
        return scene.role_text.get(state.roles[0], scene.text)
    return scene.text


def choice_label(story: Story, choice: Choice) -> str:
    """The label players see, tagged with the role for role-only choices."""
    return role_label(choice.label, [story.role_name(r) for r in choice.requires.roles])


def options_for(story: Story, state: GameState) -> list[ChoiceOption]:
    """Choices to show the player. Unmet choices are hidden unless ``show_locked``."""
    scene = story.scene(state.scene_id)
    options = []
    for c in scene.choices:
        ok = meets(c.requires, state)
        if ok or c.show_locked:
            options.append(ChoiceOption(choice=c, enabled=ok))
    return options


def choose(story: Story, state: GameState, choice_id: str) -> ChoiceResult:
    """Apply a choice and return the new state. ``state`` is not modified."""
    scene = story.scene(state.scene_id)
    choice = scene.choice(choice_id)
    if choice is None or not meets(choice.requires, state):
        raise ChoiceUnavailable(choice_id)

    inventory = list(state.inventory)
    lost = tuple(i for i in choice.takes if i in inventory)
    for item in lost:
        inventory.remove(item)
    gained = tuple(i for i in choice.gives if i not in inventory)
    inventory.extend(gained)

    flags = (set(state.flags) | set(choice.sets_flags)) - set(choice.clears_flags)

    quests = dict(state.quests)
    started = tuple(q for q in choice.starts_quests if q not in quests)
    for q in started:
        quests[q] = QUEST_ACTIVE
    completed = tuple(q for q in choice.completes_quests if quests.get(q) != QUEST_COMPLETED)
    for q in completed:
        quests[q] = QUEST_COMPLETED

    new_state = GameState(
        scene_id=choice.goto, turn=state.turn + 1, inventory=inventory, flags=flags,
        roles=list(state.roles), quests=quests,
    )
    return ChoiceResult(
        state=new_state, scene=story.scene(choice.goto), chosen=choice,
        gained=gained, lost=lost, quests_started=started, quests_completed=completed,
    )
