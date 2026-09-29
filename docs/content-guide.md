# Writing story content

> **New here?** Start with [`editing-guide.md`](editing-guide.md): how to edit the
> story on the GitHub website, step by step. The [`story-map.md`](story-map.md)
> shows every scene and path. This page is the full reference for every field.

Stories live in `content/stories/`. You don't need to touch any Python code to
write or change scenes, items or choices. You only edit YAML files, a simple
text format made of `name: value` lines where indentation matters.

> `content/stories/invisible_inn/` is the **real story**: currently a draft of
> the v1 Scholar slice. Its `story.yaml` lists the placeholder names to replace.
> For a small example of **every** feature, see the sample story in
> `tests/fixtures/stories/invisible_inn/`. The automated tests use it, so leave
> it alone unless you're changing the tests too.

## Folder layout

```
content/stories/invisible_inn/     ← one folder per story (its name is the story id)
├── story.yaml                     ← title, description, which scene comes first
├── items.yaml                     ← every item players can carry
├── quests.yaml                    ← every quest (optional)
└── scenes/
    ├── 01_arrival.yaml            ← scenes, split into as many files as you like
    └── 02_inn.yaml
```

The numbers in scene file names are only there to keep them in order. The bot
reads every `.yaml` file in `scenes/`.

## story.yaml

```yaml
title: The Invisible Inn
description: One sentence describing the story.
start_scene: arrival        # id of the first scene
min_players: 1              # for group play later (1–10)
max_players: 1

roles:                      # optional: characters players choose between
  scholar:                  # the role id: lowercase letters, numbers, _
    name: Scholar           # short name (max 20), also used to tag choices
    description: Knows a little about everything.
  mage:
    name: Mage
    description: Half-finished spells.
    playable: false         # shown as "coming soon" and can't be picked yet
```

If a story has `roles`, each game starts with a "Choose your role" message
before the first scene. At least one role must be playable.

## items.yaml

```yaml
brass_key:                  # the item id: lowercase letters, numbers, _
  name: Brass Key           # what players see
  description: Warm to the touch.
```

## quests.yaml

```yaml
find_the_innkeeper:         # the quest id: lowercase letters, numbers, _
  title: Who Runs This Place?
  description: The inn is open, but nobody is minding the desk.

restore_research:
  title: The Forbidden Research
  description: Decide what to do with the encrypted journals.
  role: scholar             # optional: a secret quest for this role only
```

Players see quests with `/quests`: the ones **in progress** (with their
description) and the ones **completed**. A quest stays hidden until a choice
starts it. Choices start and complete quests (see the next section), and each
change is announced under the next scene ("📜 New quest: …" / "✅ Quest
complete: …").

- A quest with a `role` is a **secret quest** (a private achievement). Only
  players of that role see it, in `/quests` and in the "📜 New quest" line under a
  scene. The story can still start and complete another role's secret quest.
  For example, Sable's *Clear the Air* completes when she confesses, even in a
  Scholar's game, but the Scholar never sees it. It's already in place for
  when the Rogue is playable.
- A choice can complete a quest that was never started. It then goes straight
  into the completed list.
- The validator warns about quests that nothing starts or completes.

## Scenes

Each scene has an **id** (the line it starts on), a `title`, some `text`, and
either a list of `choices` or `ending: true`.

```yaml
foyer:
  title: The Foyer
  text: |
    The moment you cross the threshold, the inn appears around you.

    Blank lines make new paragraphs. **Bold** and *italics* work too.
  choices:
    - id: ring_bell
      label: Ring the bell on the desk
      goto: innkeeper
```

- `text: |`: the `|` lets you write several lines. Indent the text under it.
- **Line breaks:** lines are joined into paragraphs, so wrap lines wherever you
  like. Leave a **blank line** to start a new paragraph. Lists (`- item`) and
  quotes (`> line`) keep their shape.
- Scene text can be up to 4,000 characters. For anything longer, split it into two scenes.
- An ending scene has `ending: true` and no choices.

### Role-specific text

A scene can have its own version of the text for a role. The role's version
**replaces** `text` for a player of that role. Roles without their own version
see `text`.

```yaml
library:
  title: The Grand Library
  text: |
    Shelves climb into the dark.          ← what everyone else sees
  role_text:
    scholar: |
      Shelves climb into the dark, sorted by a system you almost recognise.
```

In group play (later), a party with more than one role sees the shared `text`,
so write `text` so it works for everyone.

### Writing for several roles

Each player is **"you"**, and the other friends are characters in the story. So in
the Scholar's story Sable is a friend ("Sable narrows her eyes"), and in the
Rogue's story Sable *is* "you" and the Scholar (placeholder name: Tamsin) is the
friend. That means:

- **Any scene that names the player's own character needs a `role_text` for that
  role.** Otherwise the Rogue would read about "Sable" as if she were someone else.
  The plain `text` is currently the Scholar's version.
- **Any choice's `result_text` that does the same needs a `role_result_text`** (see
  the choices table). It replaces `result_text` for that role.
- **Choices about the player's own character are hidden from them with
  `not_roles`** (see Requirements): "Let Sable pick the lock" is hidden from the
  Rogue, who gets her own **[Rogue] Pick the lock**.
- **Scenes only one role can visit** (the Scholar's archive, the Rogue's vault)
  don't need versions for the others.
- The validator checks, **for each playable role**, that no scene leaves that role
  with nothing to click.

## Choices

| Field | Required? | What it does |
|---|---|---|
| `id` | yes | Short name, unique within the scene (lowercase, numbers, `_`) |
| `label` | yes | Button text players see (max 80 characters) |
| `goto` | yes | Id of the scene this leads to (can be the same scene) |
| `description` | no | Hint shown under the option in dropdown menus (max 100) |
| `result_text` | no | What happens when this is chosen, e.g. "The lock clicks." It's shown in italics at the **bottom** of the next scene, below a `---` line. Don't add your own `*` italics here: the whole thing is italic already |
| `gives` | no | Items added to the player's inventory |
| `takes` | no | Items removed from the player's inventory |
| `sets_flags` | no | Flags to remember (see below) |
| `clears_flags` | no | Flags to forget |
| `starts_quests` | no | Quests to start (they appear in `/quests`) |
| `completes_quests` | no | Quests to mark completed |
| `role_result_text` | no | A role's own version of `result_text`, e.g. `rogue: You pocket a second slice.` It replaces `result_text` for that role, and roles without one see `result_text` |
| `requires` | no | Conditions for the choice to appear (see below) |
| `show_locked` | no | `true` = show greyed-out when requirements aren't met, instead of hiding it. A choice that belongs to another role is never shown, greyed out or not |

Scenes with **up to 5 choices** show buttons. Scenes with **6–25 choices** show
a dropdown menu instead.

### Flags

Flags are true/false notes the game remembers, like `read_sign` or
`met_innkeeper`. You invent them as you go: set one with `sets_flags`, and check
it with `requires`.

### Requirements

```yaml
requires:
  items: [brass_key]        # must be carrying ALL of these
  not_items: [lantern]      # must NOT be carrying any of these
  flags: [read_sign]        # ALL of these flags must be set
  not_flags: [door_opened]  # NONE of these flags may be set
  roles: [scholar]          # only for these roles (any one of them)
  not_roles: [rogue]        # hidden from these roles
  quests_active: [find_the_innkeeper]  # these quests must be in progress
  quests_done: [restore_research]      # these quests must be completed
  not_quests_done: [restore_research]  # these quests must NOT be completed
```

A choice with `roles` is shown with the role in front of its label, e.g.
**[Scholar] Examine the runes**. The tag counts toward the 80-character limit,
and the validator checks it. `not_roles` adds **no** tag: use `roles` for
something a role *does*, and `not_roles` to hide a choice from a role it doesn't
suit (such as one about a character that role plays).

Common patterns:

- **Pick-up that disappears once taken:** `gives: [brass_key]` with
  `requires: {not_items: [brass_key]}`.
- **Locked door that teases the player:** `requires: {items: [brass_key]}` with
  `show_locked: true`.
- **One-time event:** `sets_flags: [bell_rung]` with
  `requires: {not_flags: [bell_rung]}`.
- **Something only one role can do:** `requires: {roles: [rogue]}`. Make sure
  every role still has at least one choice in the scene, or they'll get stuck
  (the validator warns you).
- **Two versions of one moment, one per role:** give each its own choice, using
  `not_roles` on the one for the other role's character and `roles` (or nothing) on
  the new one. See "Let Sable pick the lock" and "[Rogue] Pick the lock" in
  `01_arrival.yaml`.
- **A choice that finishes a quest, once:** `completes_quests: [x]` with
  `requires: {quests_active: [x]}`. It shows up while the quest is in
  progress, and disappears once it's done.
- **A quest item you carry until you hand it over:** give the item in the choice
  that starts the quest (`gives: [cuff_cipher]`), then require and take it in the
  choice that completes it (`requires: {items: [cuff_cipher]}`,
  `takes: [cuff_cipher]`). Players can see it in `/inventory` in the meantime.

## Checking your work

Run this from the repository folder:

```
python -m invisible_inn.content.validate
```

It lists every problem with the file and scene it's in: a `goto` pointing to a
scene that doesn't exist, a misspelled item, a label that's too long, and so on.
It also **warns** about scenes nothing leads to and scenes where players could
get stuck. The same check runs automatically on every pull request.

Common YAML mistakes:

- Indentation must use **spaces, not tabs**, and line up consistently.
- If a label contains a colon or starts with a quote mark, wrap the whole thing
  in quotes: `label: '"Hello," you say.'`
