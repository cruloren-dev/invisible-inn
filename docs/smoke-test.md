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

> ⚠️ **The live bot runs on Railway.** Don't start it on your computer with the same
> token while Railway is running, or both copies answer every click. Either test
> the Railway bot directly (skip the start command below), or use a separate dev
> bot with its own token in your `.env`.

```powershell
.venv\Scripts\python -m invisible_inn.content.validate   # expect "Content looks good."
.venv\Scripts\python -m pytest                           # expect all passed
.venv\Scripts\python -m invisible_inn                    # the bot itself
```

Expect log lines like `Synced 5 commands to dev server …` and `Logged in as …`.
Leave the window open; press **Ctrl+C** to stop the bot.

## 3. Feature checklist (sample story)

This checklist tests every feature with the **sample story** in
`tests/fixtures/stories/`, which doesn't change when writers edit the real
story. Start the bot with the sample story like this. The setting only lasts
until you close the PowerShell window:

```powershell
$env:CONTENT_DIR = "tests/fixtures/stories"
.venv\Scripts\python -m invisible_inn
```

To go back to the real story, close the window and open a new one, or run
`Remove-Item Env:CONTENT_DIR`. The bot's log says which story it loaded.

Play in a normal text channel. ✅ = what should happen.

| # | Do this | ✅ Expected |
|---|---|---|
| 1 | Type `/` in the channel | `/start`, `/inventory`, `/quests`, `/quit`, `/help` appear under the bot's name |
| 2 | `/help` | A "How to play" card only you can see |
| 3 | `/inventory` (no game yet) | "You don't have an adventure in progress." |
| 4 | `/start` | Private note "Your adventure awaits in #…"; a new thread with a "Choose your role" card listing Scholar, Rogue and Mage. **Mage (coming soon)** is grey |
| 4a | Click **Scholar** | The card freezes with "▶ *you* chose: Scholar"; *A Gap in the Street* with 3 buttons and the footer "The Invisible Inn · Playing as Scholar" |
| 5 | `/start` again | "You already have an adventure in progress…" with a link to the thread |
| 6 | In the thread: **Look closer at the blank sign** | The Scholar's version of the text (it mentions a "condensation cipher") and a **[Scholar] Copy the cipher before it fades** button |
| 6a | **[Scholar] Copy the cipher before it fades** | The old message freezes with "▶ *you* chose: [Scholar] Copy…". Back at the street: the line "You scribble the letters…", ➕ Cipher on Your Cuff, a Quests box with "📜 New quest: The Vanishing Letters", and the sign button is gone |
| 7 | **Step toward the laughter** | *The Foyer*, 4 buttons; **Open the green door** is grey. Quests box: "📜 New quest: Who Runs This Place?" |
| 7a | `/quests` | A card only you can see: *The Vanishing Letters · secret* and *Who Runs This Place?*, each with a description |
| 8 | **Take the brass key** | The line "You lift the key…", an Inventory box with ➕ Brass Key, the take-key button gone, and the green door now clickable |
| 9 | `/inventory` in the thread | Cipher on Your Cuff and Brass Key, with their descriptions |
| 10 | **Ring the bell** | *The Innkeeper*, with "✅ Quest complete: Who Runs This Place?" and a **[Scholar] Show the innkeeper the cipher on your cuff** button |
| 10a | **[Scholar] Show the innkeeper the cipher…**, then `/quests` | ➖ Cipher on Your Cuff, "✅ Quest complete: The Vanishing Letters" and the button is gone. `/quests` lists both quests under **Completed** |
| 10b | **"Guests welcome…"** | ➕ Glass Lantern |
| 11 | **Ask what's on tap** | *The Bar* with a **dropdown menu** ("What do you do?") instead of buttons |
| 12 | Open the menu and pick a drink | Freezes the old message, posts the bar again with the drink's line. Hints appear under each option; *A thimble of lantern oil* shows because you have the lantern |
| 13 | Click a button on an **older** message | Nothing on older frozen messages (they have no buttons). Double-clicking a live button quickly: the second click says "That moment has passed" |
| 14 | Stop the bot (Ctrl+C), start it again, then pick from the menu / click a button | Still works (buttons survive restarts) |
| 15 | **Back to the desk → Return to the foyer → Open the green door** | ➖ Brass Key, *Behind the Green Door* in green, footer "The End", no buttons |
| 16 | `/start`, then `/quit` in the new thread | "You leave the inn…" with a link back to the channel you started in, and the thread is archived and locked. Typing `/start` inside a thread also links back to that channel |
| 17 | `/start`, then `/quit` from the **main channel** | Same, and the thread is closed too |
| 18 | `/start`, pick **Rogue**, then **Look closer at the blank sign** | The ordinary sign text, and no [Scholar] button |
| 19 | As the Rogue, `/quests` before stepping inside | "You haven't discovered any quests yet." |

**Optional, needs a second account in the server:** as the second account, click
a button in someone else's game (server admins can see private threads). ✅ "This
isn't your adventure".

## 4. Story playtest (real story)

Start the bot normally (without `CONTENT_DIR`), then play the real story as the
Scholar, and again as the Rogue (section 4b below). There's no fixed script. Check that:

| # | Check | ✅ Expected |
|---|---|---|
| 1 | `/start` | Role card: **Scholar** and **Rogue** are clickable. Mage is grey "(coming soon)" |
| 1a | **[Scholar] Study the shimmering doorframe** | The storm scene again, then a `---` line and the doorframe text at the bottom, all in italics, with no stray `*` |
| 1b | **Knock**, then **Step back outside into the storm** | Back at *A Very Rude Storm*, with the storm line at the bottom |
| 2 | Play through to an ending | Every scene has a way forward. Locked choices (STAFF ONLY, the Restricted section, *Call everyone together*) unlock as described in their scenes |
| 3 | `/quests` along the way | *The Inn's Chaotic History* and *The Empty Front Desk* appear only once introduced. The Scholar's secret *The Forbidden Research* appears after taking the journal |
| 3a | Take the journal and the vial in the archive, then go to dinner | Sable asks "What's under your coat?". Later, a window onto Little Mumbling appears in the rearranged hallway |
| 3b | Confess, then help with the kettle and pour out the ink | Master Oolong appears. *Memory Is A Fickle Thing* completes. `/quests` never shows *Clear the Air* or *Cure the Kettle* (they're Sable's and Fennick's) |
| 4 | Replay with different choices | Three endings: confess (secret quest completes), keep the secret (quest stays in progress) and never take the journal |
| 5 | Reading it as a player | Note anything that feels too long, too short, unclear or not funny, and the scene it's in |

### 4b. Play it as the Rogue

`/quit` any game in progress, `/start`, and choose **Rogue**.

| # | Check | ✅ Expected |
|---|---|---|
| R1 | The whole story | You're "you", and Sable is never named in the narration. Tamsin (the Scholar) and Fennick are your friends. Footer: "Playing as Rogue" |
| R2 | The first scene | **[Rogue] Pick the lock** appears, and "Let Sable pick the lock" and the Scholar's doorframe button do not |
| R3 | Kitchen and dinner | **[Rogue] Pocket a few of the good spoons** in the kitchen. At dinner, **[Rogue] Slip out with the silver still up your sleeves** leads to a near-catch |
| R4 | Guest book, then library | The pencilled line unlocks **[Rogue] Push the book that sticks out**, which was greyed out before. No Scholar button, greyed out or not, ever appears |
| R5 | The vault door | *Clear the Air* appears in `/quests` (and only the Rogue can see it). The keyhole shows exactly the Rogue's debt |
| R6 | Dinner: **[Rogue] Break open your bread roll** | ➕ Vault Key. After dinner, **[Rogue] Follow the sound of the lock** opens the vault: a century of guests' tips and a ledger with the debt |
| R7 | The revelation | Fennick and Tamsin confess, then everyone turns to you. **Tell them about the debt** completes *Clear the Air* |
| R8 | Endings | Confess (the inn settles), keep the secret (only if you've seen the vault) or "nothing to hide" (only if you haven't). After confessing, help with the kettle and give the tips back |

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
