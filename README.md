# The Invisible Inn

A text-adventure game played in Discord. Players start an adventure with
`/start`, and the story unfolds in a private thread where they make choices
with buttons and menus.

- **For writers:** start with [docs/editing-guide.md](docs/editing-guide.md) (how to edit the story on GitHub, step by step) and the [story map](docs/story-map.md). [docs/content-guide.md](docs/content-guide.md) is the full reference for scenes, choices, items, roles and quests.
- **For developers:** [docs/architecture.md](docs/architecture.md) covers how the bot is put together and the plan for group play.

## Commands

| Command | What it does |
|---|---|
| `/start [story]` | Begin an adventure in a new private thread |
| `/inventory` | See what you're carrying (only you can see the reply) |
| `/quit` | End your current adventure and close its thread |
| `/help` | How to play |

## Running the bot locally

You'll need **Python 3.11 or newer**.

1. **Get the code and install dependencies**

   ```bash
   git clone https://github.com/cruloren-dev/invisible-inn.git
   cd invisible-inn
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. **Add your settings.** Copy `.env.example` to `.env` and fill in:
   - `DISCORD_TOKEN`: the bot token (ask the project owner; never commit it or paste it in chat)
   - `DEV_GUILD_ID`: the test server's ID, so slash commands appear instantly

3. **Run it**

   ```bash
   python -m invisible_inn
   ```

   You should see `Logged in as Invisible Inn…`. In your test server, type
   `/start` in any text channel.

   For a full step-by-step check of every command, see
   [docs/smoke-test.md](docs/smoke-test.md) (Windows PowerShell commands included).

### Discord setup checklist

This is already done for the main bot. It's listed here for reference and for anyone making their own test bot.

- Application created in the [Developer Portal](https://discord.com/developers/applications), ideally owned by a Team
- **Privileged Gateway Intents:** all off (the bot doesn't need them)
- Invite URL scopes: `bot`, `applications.commands`
- Bot permissions: View Channels, Send Messages, Send Messages in Threads,
  Create Private Threads, Manage Threads, Embed Links, Read Message History

## Development

```bash
python -m pytest                              # run the tests
python -m invisible_inn.content.validate      # check story files for mistakes
```

Both run automatically on every pull request.

Working with Claude Code? It reads [CLAUDE.md](CLAUDE.md) automatically. That
file covers the project's decisions, conventions and roadmap.

```
invisible_inn/
  __main__.py        entry point (python -m invisible_inn)
  config.py          settings from .env
  client.py          the bot: loads content, database, commands
  content/           story file format, loader and validator
  engine.py          game rules (no Discord code)
  storage.py         SQLite sessions and players
  ui.py              embeds, buttons and dropdown menus
  cogs/adventure.py  slash commands and click handling
content/stories/     story content (YAML)
tests/               automated tests
docs/                guides for writers and developers
```
