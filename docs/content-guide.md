# Writing story content

Stories live in `content/stories/`. You don't need to touch any Python code to
write or change scenes, items or choices. You only edit YAML files, a simple
text format made of `name: value` lines where indentation matters.

> The included story (`content/stories/invisible_inn/`) is **sample content**
> that shows every feature. Replace it with the real story.

## Folder layout

```
content/stories/invisible_inn/     ← one folder per story (its name is the story id)
├── story.yaml                     ← title, description, which scene comes first
├── items.yaml                     ← every item players can carry
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

## Choices

| Field | Required? | What it does |
|---|---|---|
| `id` | yes | Short name, unique within the scene (lowercase, numbers, `_`) |
| `label` | yes | Button text players see (max 80 characters) |
| `goto` | yes | Id of the scene this leads to (can be the same scene) |
| `description` | no | Hint shown under the option in dropdown menus (max 100) |
| `result_text` | no | A line shown at the top of the next scene, e.g. "The lock clicks." |
| `gives` | no | Items added to the player's inventory |
| `takes` | no | Items removed from the player's inventory |
| `sets_flags` | no | Flags to remember (see below) |
| `clears_flags` | no | Flags to forget |
| `requires` | no | Conditions for the choice to appear (see below) |
| `show_locked` | no | `true` = show greyed-out when requirements aren't met, instead of hiding it |

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
```

A choice with `roles` is shown with the role in front of its label, e.g.
**[Scholar] Examine the runes**. The tag counts toward the 80-character limit,
and the validator checks it.

Common patterns:

- **Pick-up that disappears once taken:** `gives: [brass_key]` with
  `requires: {not_items: [brass_key]}`.
- **Locked door that teases the player:** `requires: {items: [brass_key]}` with
  `show_locked: true`.
- **One-time event:** `sets_flags: [bell_rung]` with
  `requires: {not_flags: [bell_rung]}`.
- **Something only one role can do:** `requires: {roles: [rogue]}`. Make sure
  every role still has at least one choice in the scene, or they'll get stuck.

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
