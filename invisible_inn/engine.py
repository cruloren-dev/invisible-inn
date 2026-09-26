"""Game rules: what a player can do in a scene and what happens when they do it.

The engine is pure Python — no Discord, no database — so it is easy to test
and reuse (e.g. for group play later).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .content.models import Choice, Requirements, Scene, Story


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

    def to_json(self) -> str:
        return json.dumps({
            "scene_id": self.scene_id,
            "turn": self.turn,
            "inventory": self.inventory,
            "flags": sorted(self.flags),
        })

    @classmethod
    def from_json(cls, raw: str) -> "GameState":
        data = json.loads(raw)
        return cls(
            scene_id=data["scene_id"],
            turn=int(data.get("turn", 0)),
            inventory=list(data.get("inventory", [])),
            flags=set(data.get("flags", [])),
        )


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

    @property
    def finished(self) -> bool:
        return self.scene.ending


def new_game(story: Story) -> GameState:
    return GameState(scene_id=story.start_scene)


def meets(req: Requirements, state: GameState) -> bool:
    inv = set(state.inventory)
    return (
        all(i in inv for i in req.items)
        and not any(i in inv for i in req.not_items)
        and all(f in state.flags for f in req.flags)
        and not any(f in state.flags for f in req.not_flags)
    )


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
    new_state = GameState(
        scene_id=choice.goto, turn=state.turn + 1, inventory=inventory, flags=flags,
    )
    return ChoiceResult(
        state=new_state, scene=story.scene(choice.goto), chosen=choice,
        gained=gained, lost=lost,
    )
