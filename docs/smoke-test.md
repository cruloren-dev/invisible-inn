# Live smoke test

A checklist for trying the bot in a real Discord server. Automated tests use
simulated Discord objects, so run this after anything that changes how the bot
talks to Discord, and again after deploying to Railway.

Commands below are for **Windows PowerShell**, run from the repository folder.
(On macOS/Linux use `.venv/bin/python` instead of `.venv\Scripts\python`.)

## 1. One-time setup

```powershell
python --version                      # needs 3.11 or newer
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
notepad .env
```

In Notepad, fill in `DISCORD_TOKEN` and `DEV_GUILD_ID`, then save.

- Don't create `.env` with `echo ... > .env`: PowerShell saves that in a format
  Python can't read. The bot will tell you if this happens.
- `DEV_GUILD_ID` is the server's ID: in Discord, turn on
  *User Settings → Advanced → Developer Mode*, then right-click the server icon
  → *Copy Server ID*.

**Bot invite.** In the Developer Portal: *OAuth2 → URL Generator*. Tick the
scopes `bot` and `applications.commands`, then the permissions View Channels,
Send Messages, Send Messages in Threads, Create Private Threads, Manage Threads,
Embed Links and Read Message History. Open the generated link and add the bot to
the test server. (If the bot is already in the server, opening the link again
updates its permissions.)

## 2. Start the bot

```powershell
.venv\Scripts\python -m invisible_inn.content.validate   # expect "Content looks good."
.venv\Scripts\python -m pytest                           # expect all passed
.venv\Scripts\python -m invisible_inn                    # the bot itself
```

Expect log lines like `Synced 4 commands to dev server …` and `Logged in as …`.
Leave the window open; press **Ctrl+C** to stop the bot.

## 3. Checklist

Play in a normal text channel. ✅ = what should happen.

| # | Do this | ✅ Expected |
|---|---|---|
| 1 | Type `/` in the channel | `/start`, `/inventory`, `/quit`, `/help` appear under the bot's name |
| 2 | `/help` | A "How to play" card only you can see |
| 3 | `/inventory` (no game yet) | "You don't have an adventure in progress." |
| 4 | `/start` | Private note "Your adventure awaits in #…"; a new thread with a "Choose your role" card listing Scholar, Rogue and Mage. **Mage (coming soon)** is grey |
| 4a | Click **Scholar** | The card freezes with "▶ *you* chose: Scholar"; *A Gap in the Street* with 3 buttons and the footer "The Invisible Inn · Playing as Scholar" |
| 5 | `/start` again | "You already have an adventure in progress…" with a link to the thread |
| 6 | In the thread: **Look closer at the blank sign** | The Scholar's version of the text (it mentions a "condensation cipher") and a **[Scholar] Copy the cipher before it fades** button |
| 6a | **Step back into the street** | The old message freezes with "▶ *you* chose: …". Back at the street, the sign button is gone |
| 7 | **Step toward the laughter** | *The Foyer*, 4 buttons; **Open the green door** is grey |
| 8 | **Take the brass key** | The line "You lift the key…", an Inventory box with ➕ Brass Key, the take-key button gone, and the green door now clickable |
| 9 | `/inventory` in the thread | Brass Key with its description |
| 10 | **Ring the bell**, then **"Guests welcome…"** | ➕ Glass Lantern |
| 11 | **Ask what's on tap** | *The Bar* with a **dropdown menu** ("What do you do?") instead of buttons |
| 12 | Open the menu and pick a drink | Freezes the old message, posts the bar again with the drink's line. Hints appear under each option; *A thimble of lantern oil* shows because you have the lantern |
| 13 | Click a button on an **older** message | Nothing on older frozen messages (they have no buttons). Double-clicking a live button quickly: the second click says "That moment has passed" |
| 14 | Stop the bot (Ctrl+C), start it again, then pick from the menu / click a button | Still works (buttons survive restarts) |
| 15 | **Back to the desk → Return to the foyer → Open the green door** | ➖ Brass Key, *Behind the Green Door* in green, footer "The End", no buttons |
| 16 | `/start`, then `/quit` in the new thread | "You leave the inn…" with a link back to the channel you started in, and the thread is archived and locked. Typing `/start` inside a thread also links back to that channel |
| 17 | `/start`, then `/quit` from the **main channel** | Same, and the thread is closed too |
| 18 | `/start`, pick **Rogue**, then **Look closer at the blank sign** | The ordinary sign text, and no [Scholar] button |

**Optional, needs a second account in the server:** as the second account, click
a button in someone else's game (server admins can see private threads). ✅ "This
isn't your adventure".

## If something goes wrong

Copy the error lines from the bot's window (never the token) and note which step
failed. Common ones:

| Symptom | Likely cause |
|---|---|
| "Configuration problem: DISCORD_TOKEN is not set" | `.env` missing, or not in the repository folder |
| "Discord rejected the token" | Token was reset or pasted wrongly: reset it in the Developer Portal |
| "Discord refused to add slash commands…" | Wrong `DEV_GUILD_ID`, or bot invited without `applications.commands` |
| Commands appear twice | Bot was once run without `DEV_GUILD_ID`, so global copies exist too. Harmless for testing |
| "I need the Create Private Threads…" | Channel permissions: check the bot's role on that channel |
| "This interaction failed" under a button | Check the bot window for an error and report it |
