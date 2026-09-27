# How to edit the story

A step-by-step guide for writers. You don't need to install anything or know how
to code: everything happens on the GitHub website. For the full list of what
every field does, see the **writers' reference**, [`content-guide.md`](content-guide.md).

## Before you start

1. Create a free account at **github.com** if you don't have one.
2. Ask the project owner to invite you to the **invisible-inn** repository.
   You'll get an email: click **Accept invitation**.
3. Have a look at the **story map**, [`story-map.md`](story-map.md). It shows every
   scene, how they connect, what's locked, and each choice in detail. It updates
   itself whenever changes are merged.

## Where everything lives

All story files are in **`content/stories/invisible_inn/`**:

| File | What's in it |
|---|---|
| `story.yaml` | The title, the first scene, the roles, and the list of **placeholder names** still to replace |
| `items.yaml` | Every item (name and description) |
| `quests.yaml` | Every quest (title, description, and which role a secret quest belongs to) |
| `scenes/01_arrival.yaml` | Milestone 1: the storm, the foyer, the kitchen |
| `scenes/02_main_hall.yaml` | Milestone 2: the main hall and the Welcome Scroll |
| `scenes/03_parlor.yaml` | Milestone 3: the parlour and the guest book |
| `scenes/04_library.yaml` | Milestones 3 and 5: the library and the Scholar's archive |
| `scenes/05_study.yaml` | Milestone 4: the innkeeper's study and message |
| `scenes/06_revelation.yaml` | Milestone 8 (slice version) and the three endings |

To find a scene, look it up in the story map. Each scene there shows its id and file.

## Making a change, step by step

### 1. Open the file

1. Go to **github.com/cruloren-dev/invisible-inn**.
2. Click **content**, then **stories**, then **invisible_inn**, then **scenes**.
3. Click the file you want, for example `03_parlor.yaml`.

### 2. Edit it

1. Click the **pencil icon** ✏️ (top right of the file). If you don't see it,
   your invitation hasn't been accepted yet.
2. Make your changes. Check the rules below (indentation matters).
3. Click **Preview** if you want to see what changed (shown in green and red).

### 3. Submit it for review

1. Click the green **Commit changes…** button.
2. In **Commit message**, write a short summary, e.g. `Funnier guest book entries`.
3. Choose **Create a new branch for this commit and start a pull request**.
   Give the branch a short name, e.g. `guest-book-jokes`. **Don't** choose
   "Commit directly to the main branch".
4. Click **Propose changes**, then **Create pull request** on the next page. Add
   a sentence about what you changed and why.

### 4. Check the result

After a minute, a check called **CI** appears at the bottom of the pull request:

- ✅ **Green tick:** the story is valid. The owner can review and merge it.
- ❌ **Red cross:** something needs fixing. Click **Details** next to the check,
  then open **Check story content**. It lists each problem with its file and
  scene, e.g. `03_parlor.yaml › guest_book_parlor › open_book: goto 'guest_bok'
  is not a scene that exists`.

**Seeing your change on the map:** click **Details** on the CI check, then
**Summary** (top left). The story map there includes your change, so you can
check your new paths connect the way you meant.

### 5. Fix problems (if needed)

You can keep editing the same pull request:

1. In the pull request, click the **Files changed** tab.
2. Next to the file, click **⋯**, then **Edit file**.
3. Fix it and click **Commit changes**. Keep **Commit directly to the
   `your-branch-name` branch** selected. That updates the same pull request, and
   the check runs again.

To change **several files** in one pull request, make your first edit as above,
then switch to your branch (the branch menu at the top left of the file list
says `main`; pick your branch) and edit the other files there, committing
directly to your branch each time.

### 6. After it's merged

When the owner merges your pull request, the bot updates itself within a couple
of minutes (it's briefly offline while it restarts), and the story map updates
itself shortly after.

## Recipes

Copy these and change the words. Indentation uses **spaces, never tabs**, and
must line up exactly like the examples.

**Change some text:** just edit the words under `text: |`. Keep the indentation.
Wrap lines wherever you like; leave a **blank line** to start a new paragraph.

**Add a choice** to a scene (inside its `choices:` list):

```yaml
    - id: pet_the_cat               # unique within the scene: a-z, 0-9, _
      label: Pet the suspicious cat # the button text (max 80 characters)
      goto: main_hall               # the scene it leads to
      result_text: The cat allows it. Once.
```

**Add a scene** (at the end of a scenes file, not indented):

```yaml
dining_room:
  title: The Dining Room
  text: |
    A long table set for exactly three.
  choices:
    - id: sit_down
      label: Sit down
      goto: main_hall
```

Then add a choice somewhere else that leads to it (`goto: dining_room`),
otherwise players can never reach it. The checker warns you if you forget.

**A choice only the Scholar sees:**

```yaml
      requires:
        roles: [scholar]
```

**A locked path that opens once you have an item** (shown greyed out until then):

```yaml
      requires:
        items: [guest_book]
      show_locked: true
```

**Something that can only happen once:** give it a flag, and hide it once the
flag is set:

```yaml
      sets_flags: [rang_the_bell]
      requires:
        not_flags: [rang_the_bell]
```

More patterns (items, quests, role text) are in [`content-guide.md`](content-guide.md).

## Rules that avoid trouble

- **Spaces, not tabs**, and keep the indentation lined up.
- If a label or text **starts with a quote mark** or contains `: ` (colon and
  space), wrap the whole thing in single quotes: `label: '"Hello," you say.'`
- **Don't use `*` in `result_text`.** It's shown in italics automatically.
- **Changing an `id` is a bigger change than it looks.** Other scenes point to
  it, and games that are saved in a scene whose id changed can't continue (the
  player has to `/quit`). Change titles and text freely; change ids only when you
  mean to, and fix every `goto` that used the old one (the checker lists them).
- Every scene needs at least one choice that **every role** can take, or a role
  could get stuck. The checker warns about scenes where every choice has a
  condition.

## Open story questions

These are the questions for writers to work out before Claude builds more.
Answer them however suits you (in a pull request, a GitHub issue, or by telling
the project owner), and change the story directly where the answer is text.

1. **Placeholder names.** Replace or confirm: **Sable** (Rogue), **Fennick**
   (Mage), **Madame Thistlewick** (the innkeeper), **Little Mumbling** and **memory
   ink** (the Scholar's past), the **kettle** (Fennick's mentor), the **vault**
   (Sable's secret). The list is at the top of `story.yaml`.
2. **Length.** The slice plays in about 15–20 minutes; the goal is 20–30.
   Milestones 6–7 (the dining-room conflict, and the inn reacting to the
   friends' choices) aren't written yet. What happens in them? Even a list of
   beats is enough for Claude to draft from.
3. **The Scholar's secret.** Does the memory-ink / lost-Tuesdays secret work?
   Can the Scholar *nearly get caught* with the journal before the revelation?
4. **Endings of the slice.** Are three endings right (confess, keep the secret,
   never find the journal)? Should keeping the secret have consequences in later
   chapters?
5. **The Forbidden Research as a multi-step quest.** Multi-step quests are
   planned. What would the steps of this quest be?
6. **The Rogue and Mage paths.** Each needs its own route through the library
   (Sable's vault, Fennick's kettle) and its own secret room before they can be
   played. Where do their secrets start and resolve?
7. **Revelation with several players.** In the slice, Sable and Fennick confess
   as background characters. In multiplayer they may be real players. How should
   the revelation work then?
8. **Tone and pacing.** Read it on a phone as well as a computer. Mark any scene
   that feels too long, too short, unclear, or not funny enough.
