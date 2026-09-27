# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**The Invisible Inn** is a Discord text-adventure bot. Players type `/start`, get a
private thread, and play through pre-written scenes by clicking buttons or
dropdown options.

The project owner is a **project manager, not a developer**, working on
**Windows (PowerShell)**. When explaining things to them, use plain language and
give copy-pasteable Windows/PowerShell commands (e.g. `.venv\Scripts\python`).

Read these before making significant changes:
- `docs/story-and-mechanics-design.md`: the story plan and the new mechanics it
  needs. **Its "v1 scope" box at the top is the agreed plan for v1**. The rest of
  that document is the long-term vision.
- `docs/architecture.md`: layers, game flow, data model, group-play plan, Railway notes
- `docs/content-guide.md`: the YAML story format (the writers' reference)

## Decisions already made (v1). Don't change these without asking.

| Area | Decision |
|---|---|
| Play mode | Solo first. Group play (2–10 players, most often 2–4) comes later, so keep things group-ready |
| Where games happen | A private thread per game, created from a shared text channel |
| Input | Slash commands + buttons / dropdown menus. **No** free-text parsing |
| Distribution | Private bot (one test server for now) |
| Stack | Python 3.11+, discord.py 2.x |
| Content | Scenes, choices and items in YAML under `content/stories/`, separate from code |
| Storage | SQLite via built-in `sqlite3` + `asyncio.to_thread` (no aiosqlite) |
| Hosting | Local now, Railway later |
| Narration | Pre-written text only. **No** AI-generated narration |
| Roles | Players pick Scholar, Rogue or Mage. Scholar content comes first |
| Multiplayer role visibility | Role choices are visible to all players and labelled with the role. Only secret-quest details are private |
| Multiplayer conflicts | The first player to choose decides where the story goes |
| Quests | A real quest system (active / completed, only shown once introduced). v1 has 1 Scholar quest; it will grow to 10 per role |
| Story text | Claude may draft scenes. The owner edits them and has the final say |

## Commands

On Windows, run these from the repo root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest                            # all tests
.venv\Scripts\python -m invisible_inn.content.validate    # check story YAML
.venv\Scripts\python -m invisible_inn                     # run the bot (needs .env)
```

On macOS/Linux, use `.venv/bin/python` instead.

CI (`.github/workflows/ci.yml`) runs the content validator and pytest on every PR,
with `REQUIRE_DISCORD=1` so the Discord tests can't silently skip.

## Layout

```
invisible_inn/
  __main__.py        entry point; friendly errors for missing token / bad content
  config.py          env settings: DISCORD_TOKEN, DEV_GUILD_ID, DATABASE_PATH, CONTENT_DIR, LOG_LEVEL
  client.py          InnBot: loads content, runs DB migrations, registers DynamicItems, syncs commands
  content/           models.py (dataclasses), loader.py (YAML + validation), validate.py (CLI)
  engine.py          pure game rules: GameState, options_for(), choose()
  storage.py         SQLite: sessions + session_players, MIGRATIONS list
  ui.py              embeds, ChoiceButton / ChoiceSelect DynamicItems
  cogs/adventure.py  /start /inventory /quit /help + handle_choice()
content/stories/<story_id>/   story.yaml, items.yaml, scenes/*.yaml
tests/               unittest-style tests (run with pytest)
```

**Layering rule:** `content/` and `engine.py` must not import discord or touch the
DB. `storage.py` must not import discord. Only `ui.py`, `cogs/` and `client.py` know
about Discord. Keep it this way so game logic stays unit-testable.

## Conventions and gotchas

- **Secrets:** the token lives only in `.env`, which is gitignored. Never commit it,
  print it, log it, or ask the user to paste it into chat.
- **No privileged intents.** `discord.Intents.default()` only. Adding Message
  Content, Members or Presence needs a discussion first.
- **Button custom_ids are a contract.** Formats: `inn:c:<session>:<turn>:<choice_id>`
  and `inn:s:<session>:<turn>`. Messages already posted in Discord carry the old
  ids, so if you change a format, keep the old one working too. Custom ids are
  limited to 100 characters.
- **Turn numbers** in custom_ids make stale clicks and double-clicks harmless. Every
  state change must go through `engine.choose()`, which increments `turn`.
- **Per-session `asyncio.Lock`** in the cog serialises clicks. Keep DB writes inside it.
- **Authorisation** checks `storage.is_player()`, not "is owner". This is deliberate,
  for group play. `/quit` is owner-only.
- **DB migrations:** append a new SQL string to `MIGRATIONS` in `storage.py`. Never
  edit or reorder existing entries. They're tracked by `PRAGMA user_version`.
- **Content limits** are enforced by the loader: ids must match `[a-z0-9_]{1,32}`,
  labels ≤80, option descriptions ≤100, scene text ≤4000, ≤25 choices. Scenes with
  ≤5 choices render as buttons and 6–25 as a dropdown. Dropdowns hide locked choices
  because they can't grey out a single option.
- **New content fields:** add them to the model, the loader's allowed-keys sets
  (`CHOICE_KEYS` / `SCENE_KEYS`) and validation, `docs/content-guide.md`, and tests.
  The loader rejects unknown keys on purpose, to catch writer typos.
- **Sample content:** `content/stories/invisible_inn/` is placeholder content that
  shows every feature. Tests depend on its scene and choice ids (`arrival`,
  `foyer`, `take_key`, `green_door`, …). If writers replace it, move the tests to a
  fixture story under `tests/`.
- **Tests** use `unittest` (with `IsolatedAsyncioTestCase` for async) and run
  under pytest. Discord-facing tests use fake interaction objects; see
  `tests/test_adventure_flow.py`.

## Workflow

- The owner reviews everything through **pull requests**. Work on a branch, open a
  PR, and never push directly to `main`.
- Add or update tests with every change, and run pytest and the validator before
  opening a PR.
- Keep `docs/` in sync: `content-guide.md` for format changes, `architecture.md`
  for design changes.
- PR descriptions should be readable by a non-developer: what changed, how to try
  it, and what's left open.

## Status and roadmap

**Done (PR #1, merged):** the framework, the YAML content format and validator, the
engine, SQLite storage, `/start` `/inventory` `/quit` `/help`, buttons and
dropdowns that survive restarts, a sample story, docs, tests and CI.

**Also done:** the live smoke test was started on the owner's test server (the bot
connects and syncs commands). PR #4 made `/quit` and `/start` inside a thread link
back to the game's channel. Story and mechanics design is agreed: see
`docs/story-and-mechanics-design.md`.

**Next: v1 (solo), roughly in order:**
1. **Roles:** pick a role at the start of a game, role-locked and labelled
   choices, and role-specific scene text.
2. **Quests:** quests defined in YAML, started and completed by choices, and a
   `/quests` command. Build it so secret quests can grow to 10 per role.
3. **Content:** move the sample story to a test fixture, then draft the Scholar
   playable slice for the owner to edit.
4. Finish the live smoke test with the new content.

**After v1:** multiplayer (v1.1, see the design doc's v1 scope box and the open
questions in `docs/architecture.md`), then **Railway deployment**, which needs a
persistent volume for SQLite (`DATABASE_PATH=/data/...`) and only one running
instance.
