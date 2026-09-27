# Hosting the bot on Railway

Railway runs the bot around the clock, so people can play without your computer
being on. Every change merged into `main` is deployed automatically.

You'll need about 20 minutes, your GitHub account, and access to the Discord
Developer Portal.

## Before you start

- The pull request that adds `railway.json` must be merged. It tells Railway how
  to start the bot.
- **Only one copy of the bot may run at a time.** If the bot is also running on
  your computer (or in a Claude Code session), both copies answer every click and
  games get confused. Stop the local copy before step 6.
- Games played on your computer so far won't move to Railway. It starts with an
  empty database.

## 1. Create a Railway account

1. Go to **railway.com** and click **Login → Login with GitHub**.
2. Approve the permissions GitHub shows.
3. Choose a plan. A bot that runs all the time needs the **Hobby** plan, which is
   paid monthly (check the current price on Railway's pricing page). The free
   trial is fine for trying it out.

## 2. Create the project from GitHub

1. In Railway, click **New Project → Deploy from GitHub repo**.
2. If Railway asks to install its GitHub app, choose **Only select repositories**,
   pick **invisible-inn** and click **Install**.
3. Choose **cruloren-dev/invisible-inn**.

Railway starts building straight away. **The first attempt will fail or crash**
because it doesn't have the bot token yet. That's expected.

## 3. Add the settings (variables)

Click the **invisible-inn** box on the project canvas, then the **Variables** tab.
Add these with **New Variable**:

| Name | Value |
|---|---|
| `DISCORD_TOKEN` | The bot token (see below) |
| `DEV_GUILD_ID` | Your test server's ID, the same as in your `.env` |
| `DATABASE_PATH` | `/data/invisible_inn.db` |

**The token:** you can copy it from your `.env` file (open it with
`notepad .env` in the project folder), or get a fresh one in the Developer Portal
(**Bot → Reset Token**). If you reset it, update your `.env` too. Paste it only
into Railway. Never paste it into chat, a pull request or any other file.

`DEV_GUILD_ID` keeps the commands in your test server. For a private bot in one
server, keep it set.

## 4. Add a volume (where saved games live)

Without a volume, every update would wipe all saved games.

1. On the project canvas, right-click an empty area and choose **Volume** (or
   press **Ctrl+K** and type "volume").
2. Attach it to the **invisible-inn** service.
3. Set the **mount path** to `/data`.

## 5. Check the service settings

In the service's **Settings** tab:

- **Deploy → Start command** should show `python -m invisible_inn`, taken from
  `railway.json`.
- **Replicas** should be **1**.
- **Networking:** the bot doesn't need a public domain. Leave it without one.
- *(Recommended)* If there's an option like **Wait for CI** under the source
  section, turn it on. Railway then only deploys once GitHub's checks (tests and
  story checker) have passed.

## 6. Stop the local bot, then deploy

1. Stop the bot on your computer: press **Ctrl+C** in its window, or ask Claude
   to stop it.
2. In Railway, click **Deploy** (or **Redeploy** on the latest deployment) if
   it hasn't restarted by itself after you added the variables and volume.

## 7. Check it's running

1. Open the **Deployments** tab and click the newest deployment, then **View logs**.
2. Look for:
   - `Loaded 1 story/stories: invisible_inn`
   - `Synced 5 commands to dev server …`
   - `Logged in as Invisible Inn#…`
3. In Discord, the bot should show as online. Try `/start`.

## After that: how updates work

Merge a pull request into `main`, and Railway rebuilds and restarts the bot within
a couple of minutes. The bot is briefly offline while it restarts. Saved games
survive because they're on the volume, and buttons keep working.

## If something goes wrong

| Symptom in the logs | Likely cause |
|---|---|
| "DISCORD_TOKEN is not set" | Variable missing or misspelled. Check the Variables tab |
| "Discord rejected the token" | The token was reset or pasted with extra spaces. Paste a fresh one |
| "Discord refused to add slash commands…" | Wrong `DEV_GUILD_ID` |
| Saved games vanish after an update | The volume isn't mounted at `/data`, or `DATABASE_PATH` is wrong |
| Every click is answered twice, or "That moment has passed" | A second copy is running, probably on your computer. Stop it |
| Build fails | Open the build logs and copy the error lines (never the token) to Claude |

## Testing changes before they go live

While Railway runs the real bot, don't run the same bot on your computer. To test
locally, create a second bot in the Developer Portal (e.g. "Invisible Inn (Dev)"),
invite it to the test server, and put *its* token in your local `.env`. Ask
Claude to help when you get there.
