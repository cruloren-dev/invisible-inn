"""Turn game state into Discord messages: embeds, buttons and dropdown menus.

Buttons and menus use ``DynamicItem``: their ``custom_id`` encodes which game
session, turn and choice they belong to. That means they keep working after the
bot restarts — no in-memory view state is needed.

custom_id formats (Discord allows up to 100 characters):
    inn:c:<session_id>:<turn>:<choice_id>    a choice button
    inn:s:<session_id>:<turn>                a choice dropdown menu
    inn:r:<session_id>:<role_id>             a role-picker button
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from .content.models import Story
from .engine import ChoiceResult, GameState, choice_label, options_for, scene_text

if TYPE_CHECKING:
    from .cogs.adventure import Adventure

EMBED_COLOUR = discord.Colour(0x6B4E9B)
ENDING_COLOUR = discord.Colour(0x3E7C59)
MAX_BUTTONS = 5  # one row; more choices than this switch to a dropdown menu
EMBED_DESCRIPTION_LIMIT = 4096

BUTTON_TEMPLATE = r"inn:c:(?P<session>\d+):(?P<turn>\d+):(?P<choice>[a-z0-9_]+)"
SELECT_TEMPLATE = r"inn:s:(?P<session>\d+):(?P<turn>\d+)"
ROLE_TEMPLATE = r"inn:r:(?P<session>\d+):(?P<role>[a-z0-9_]+)"


def _adventure(interaction: discord.Interaction) -> "Adventure":
    cog = interaction.client.get_cog("Adventure")  # type: ignore[attr-defined]
    if cog is None:
        raise RuntimeError("Adventure cog is not loaded")
    return cog


class ChoiceButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=BUTTON_TEMPLATE,
):
    def __init__(self, session_id: int, turn: int, choice_id: str, *,
                 label: str | None = None, enabled: bool = True):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary if enabled else discord.ButtonStyle.secondary,
                disabled=not enabled,
                custom_id=f"inn:c:{session_id}:{turn}:{choice_id}",
            )
        )
        self.session_id, self.turn, self.choice_id = session_id, turn, choice_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["session"]), int(match["turn"]), match["choice"], label=item.label)

    async def callback(self, interaction: discord.Interaction) -> None:
        await _adventure(interaction).handle_choice(interaction, self.session_id, self.turn, self.choice_id)


class ChoiceSelect(
    discord.ui.DynamicItem[discord.ui.Select],
    template=SELECT_TEMPLATE,
):
    def __init__(self, session_id: int, turn: int, options: list[discord.SelectOption] | None = None):
        super().__init__(
            discord.ui.Select(
                placeholder="What do you do?",
                options=options or [discord.SelectOption(label="…", value="_")],
                custom_id=f"inn:s:{session_id}:{turn}",
            )
        )
        self.session_id, self.turn = session_id, turn

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["session"]), int(match["turn"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        values = (interaction.data or {}).get("values") or []
        if not values:
            await interaction.response.defer()
            return
        await _adventure(interaction).handle_choice(interaction, self.session_id, self.turn, values[0])


class RoleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=ROLE_TEMPLATE,
):
    def __init__(self, session_id: int, role_id: str, *, label: str | None = None, enabled: bool = True):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary if enabled else discord.ButtonStyle.secondary,
                disabled=not enabled,
                custom_id=f"inn:r:{session_id}:{role_id}",
            )
        )
        self.session_id, self.role_id = session_id, role_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["session"]), match["role"], label=item.label)

    async def callback(self, interaction: discord.Interaction) -> None:
        await _adventure(interaction).handle_role(interaction, self.session_id, self.role_id)


def render_role_picker(story: Story, session_id: int) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(title=story.title, description=story.description or None, colour=EMBED_COLOUR)
    for role in story.roles.values():
        name = role.name if role.playable else f"{role.name} (coming soon)"
        embed.add_field(name=name, value=role.description or "​", inline=False)
    embed.set_footer(text="Who are you? Choose your role to begin.")
    view = discord.ui.View(timeout=None)
    for role in story.roles.values():
        label = role.name if role.playable else f"{role.name} (coming soon)"
        view.add_item(RoleButton(session_id, role.id, label=label, enabled=role.playable))
    return embed, view


def build_choice_view(story: Story, state: GameState, session_id: int) -> discord.ui.View | None:
    options = options_for(story, state)
    if not options:
        return None
    view = discord.ui.View(timeout=None)
    if len(options) <= MAX_BUTTONS:
        for opt in options:
            view.add_item(ChoiceButton(
                session_id, state.turn, opt.choice.id, label=choice_label(story, opt.choice), enabled=opt.enabled,
            ))
    else:
        # Dropdown menus can't grey out a single option, so locked choices are left out.
        select_options = [
            discord.SelectOption(label=choice_label(story, o.choice), value=o.choice.id,
                                 description=o.choice.description)
            for o in options if o.enabled
        ]
        if not select_options:
            return None
        view.add_item(ChoiceSelect(session_id, state.turn, select_options))
    return view


def scene_embed(story: Story, state: GameState, result: ChoiceResult | None = None) -> discord.Embed:
    scene = story.scene(state.scene_id)
    text = scene_text(scene, state)
    if result and result.chosen.result_text:
        text = f"*{result.chosen.result_text.strip()}*\n\n{text}"
    if len(text) > EMBED_DESCRIPTION_LIMIT:
        text = text[: EMBED_DESCRIPTION_LIMIT - 1] + "…"

    embed = discord.Embed(
        title=scene.title, description=text,
        colour=ENDING_COLOUR if scene.ending else EMBED_COLOUR,
    )
    if result and (result.gained or result.lost):
        lines = [f"➕ {story.item_name(i)}" for i in result.gained]
        lines += [f"➖ {story.item_name(i)}" for i in result.lost]
        embed.add_field(name="Inventory", value="\n".join(lines), inline=False)

    if scene.ending:
        embed.set_footer(text="The End · use /start to play again")
    elif not options_for(story, state):
        embed.set_footer(text="There's nothing you can do here. Use /quit to end this adventure.")
    else:
        embed.set_footer(text=f"{story.title} · {party_text(story, state)}" if state.roles else story.title)
    return embed


def party_text(story: Story, state: GameState) -> str:
    return "Playing as " + " & ".join(story.role_name(r) for r in state.roles)


def render_scene(story: Story, state: GameState, session_id: int,
                 result: ChoiceResult | None = None) -> tuple[discord.Embed, discord.ui.View | None]:
    embed = scene_embed(story, state, result)
    view = None if story.scene(state.scene_id).ending else build_choice_view(story, state, session_id)
    return embed, view


def inventory_embed(story: Story, state: GameState) -> discord.Embed:
    embed = discord.Embed(title="Inventory", colour=EMBED_COLOUR)
    if not state.inventory:
        embed.description = "Your pockets are empty."
    for item_id in state.inventory:
        item = story.items.get(item_id)
        embed.add_field(
            name=item.name if item else item_id,
            value=(item.description if item and item.description else "​"),
            inline=False,
        )
    return embed
