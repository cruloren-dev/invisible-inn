# Architecture

## Decisions (v1)

| Area | Decision |
|---|---|
| Play mode | Solo first; built so 2–10 player groups can be added later |
| Where games happen | A private thread per game, created from a shared channel |
| Input | Slash commands + buttons / dropdown menus (no free-text parsing) |
| Distribution | Private bot, test server first |
| Language | Python 3.11+, discord.py 2.x |
| Content | Scenes, choices and items in YAML files, separate from code |
| Storage | SQLite (Python's built-in `sqlite3`) |
| Hosting | Local first, then Railway |
| Narration | Pre-written story text only (no AI generation) |

Because we use no privileged gateway intents (Message Content, Members,
Presence), the bot needs no special approval from Discord.

## Layers

```
content/stories/*.yaml
        │  loaded & validated at startup
        ▼
invisible_inn/content/   models + loader + validator       (no Discord, no DB)
invisible_inn/engine.py  game rules: options, choose()      (no Discord, no DB)
invisible_inn/storage.py SQLite sessions & players          (no Discord)
invisible_inn/ui.py      embeds, buttons, dropdown menus    (Discord)
invisible_inn/cogs/      slash commands, click handling     (Discord)
invisible_inn/client.py  wires it all together
```

The engine and content layers don't know about Discord, so they are fully unit
tested. They could also back a different front end (such as a web preview for
writers) without changes.

## Game flow

1. `/start` in a text channel creates a **private thread**, adds the player,
   creates a session row and posts the first scene. If the story defines
   **roles**, it posts a role picker first. `Adventure.handle_role` saves the
   chosen role in `GameState.roles`, freezes the picker and posts the first scene.
2. Each scene is an embed with buttons (≤5 choices) or a dropdown menu (6–25).
3. A click is handled by `Adventure.handle_choice`. It checks that the session is
   active, that the clicker is a player, and that the click is for the current
   turn. Then it applies `engine.choose`, saves the new state, freezes the old
   message ("▶ Kelsey chose: …") and posts the next scene.
4. Ending scenes mark the session `finished`. `/quit` marks it `abandoned` and
   archives and locks the thread.

### Buttons that survive restarts

Buttons use discord.py `DynamicItem`s. The button's `custom_id` carries
everything needed to handle the click:

```
inn:c:<session_id>:<turn>:<choice_id>
inn:s:<session_id>:<turn>              (dropdown; the choice is the selected value)
inn:r:<session_id>:<role_id>           (role picker; no turn: a second pick is refused
                                        because a role is already set)
```

Nothing is kept in memory between clicks, so a restart (or a Railway redeploy)
doesn't break games in progress. The `turn` number makes clicks on old messages
and double-clicks harmless.

## Data model

```
sessions         id, guild_id, channel_id, thread_id, owner_id, story_id,
                 state (JSON), status (active|finished|abandoned), timestamps
session_players  session_id, user_id, role (owner|player)
```

`state` is `GameState` as JSON: `{scene_id, turn, inventory[], flags[], roles[]}`.
Missing keys get defaults, so games saved before a field existed still load.

### Roles

`GameState.roles` is the **party's** roles: one in solo play, and up to one per
player in group play. The engine uses it to:

- show a choice with `requires: {roles: [...]}` only if one of those roles is in
  the party (`engine.meets`);
- tag such choices with the role, e.g. "[Scholar] …" (`engine.choice_label`). The
  agreed group-play rule is that role choices are visible to everyone and labelled;
- use a scene's `role_text` for a party of exactly one role, and the shared `text`
  otherwise (`engine.scene_text`).

For group play, the click handler will also need to check that the clicker plays
the choice's role. That means storing which player has which role (e.g. a new
`session_players` column, added through a migration).

Schema changes are appended to `MIGRATIONS` in `storage.py` and applied
automatically at startup (tracked with `PRAGMA user_version`).

## Path to group play

The pieces are already in place:

- Sessions have a **player list** (`session_players`), and click handling
  already checks "is this user a player?" rather than "is this the owner?".
- Threads are private, so the game only needs to add invited users to the thread.
- Stories declare `min_players` / `max_players`.

Still to design and build:

- `/invite @user` and a lobby or "ready" step before the game starts
- How a group decides: **agreed: the first click wins** (see the design doc's
  v1 scope box). Choices that wait for every player are still to be designed
- Per-player vs shared inventory (this would extend `GameState`)
- Whose name appears on "▶ X chose: …"

## Moving to Railway

- Run command: `python -m invisible_inn`
- Set `DISCORD_TOKEN` (and leave `DEV_GUILD_ID` blank for global commands, or
  set it if the bot stays in one server) in Railway's variables.
- SQLite needs a **persistent volume**. Mount one (e.g. at `/data`) and set
  `DATABASE_PATH=/data/invisible_inn.db`. Otherwise the database is wiped on
  every deploy.
- Only run **one** instance of the bot at a time.
