# Story & Mechanics Design: The Invisible Inn

> ## v1 scope (agreed 2026-09-27)
>
> The rest of this document is the full vision. **v1 builds only this part of it.**
> Where this box disagrees with the sections below, this box wins.
>
> **v1 is solo play.** Multiplayer is the next release (v1.1).
>
> **In v1:**
> - **Role choice.** The player picks Scholar, Rogue or Mage when a game starts. The
>   **Scholar** was written and playable first, and the **Rogue** followed
>   (2026-09-29). The Mage is shown as "coming soon" until their content exists.
> - **Role-locked choices**, labelled with the role, e.g. "[Scholar] Examine the runes".
> - **Role-specific scene text**, falling back to the shared text.
> - **Quests.** `/quests` shows the player's active and completed quests. A quest
>   only appears once the story has introduced it. v1 has **one secret quest for
>   the Scholar**, but the feature is built as a proper quest system so it can grow
>   to 10 secret quests per role, plus shared quests.
> - **Content:** the 20–30 minute playable slice from the Writing Plan, Scholar
>   path. Claude drafts the scene text from this plan, and the project manager
>   edits it and has the final say.
>
> **Scene text** mentions all three friends (Scholar, Rogue, Mage) whoever is
> playing. The friends who aren't being played are background characters. The
> story must never depend on three people being available at the same time.
>
> **Decided for multiplayer (v1.1), not built in v1:**
> - **Roles are visible to everyone** (option b). Role choices are shown to all
>   players and labelled with the role. Only the details of secret quests are private.
> - **When players choose differently, the first click decides** where the story
>   goes. Later choices on the same scene only add their result text.
> - The game supports 1–3 players. A missing role becomes a background character.
>
> **Later (v1.1 and beyond):** multiplayer sessions and invites, choices that wait for
> every player, secret-quest notifications, agreeing on an ending, what to do when a
> player goes idle, the Rogue and Mage paths, secret quests 2–10, and the remaining
> milestones.
>
> **Multi-step quests (requested 2026-09-27, future version):** quests will
> usually take several steps to complete. `/quests` should show progress through
> the steps. In v1 a quest is started and completed by single choices, and writers
> can approximate steps with flags and items.

## Summary

**Premise:** Three old friends—a Scholar, a Rogue, and a Mage—are caught in a storm and stumble upon The Invisible Inn, a mysterious sanctuary that appears to those who need it most. They discover the innkeeper has abandoned the place and left them a cryptic task: tend to the inn, and it will tend to you. Together, they must explore the inn's secrets, confront their chaotic pasts, and decide whether they're ready to take over as its new caretakers.

**Tone:** Quirky, cozy, and comedic. Light fantasy with whimsy and humor. The tone balances vulnerability with comedy—the characters are dealing with real emotional stakes (past mistakes, major life changes) but wrapped in absurdist situations and witty banter.

**Audience:** Adult players interested in collaborative, light fantasy adventures. No dark elements. Humor leans toward situational comedy and character-driven jokes rather than slapstick.

**Target Playthrough Length:** 60 minutes for cooperative 2-player playthroughs; solo playthroughs follow the same story with adjusted mechanics.

---

## Story Structure

### Five Acts & Ten Major Milestones

**ACT 1: The Storm & The Ridiculous Sanctuary**
- **Milestone 1:** Arrival at the Invisible Inn
- **Milestone 2:** Welcome to the Abandoned Chaos (Find the Welcome Scroll)

**ACT 2: Exploring the Delightfully Weird**
- **Milestone 3:** The Inn's Greatest Hits (Discover the Guest Book & Previous Guests)
- **Milestone 4:** The Innkeeper's Dramatic Departure (Find the Innkeeper's Study & Video Message)

**ACT 3: When Secrets Become Slightly Awkward**
- **Milestone 5:** The Skeletons in the Closet (Each Role Discovers Their Secret Quest)
- **Milestone 6:** Conflicting Motivations & Sneaky Shenanigans (Secret Quests Create Tension)

**ACT 4: Chaos, Comedy, and Commitment**
- **Milestone 7:** The Inn Has Opinions (And They're Weird) – The inn responds to choices
- **Milestone 8:** The Grand Revelation & Messy Resolution (All Secrets Come to Light)

**ACT 5: New Chaos, New Beginnings**
- **Milestone 9:** The Inn's First New Guest (A Chaotic New Arrival)
- **Milestone 10:** The Final Pact & Multiple Endings (Consensus-Based Ending Choice)

---

### Scene Map (Planned)

| Scene ID | Milestone | Purpose | Key Choices | Leads To |
|----------|-----------|---------|------------|----------|
| `arrival_storm` | 1 | The three friends discover the inn during the storm | Seek shelter / Investigate first | `foyer_arrival` |
| `foyer_arrival` | 1 | Enter the inn, warm up, initial wonder | Explore library / Explore kitchen / Rest by fire | `main_hall` |
| `main_hall` | 2 | Central hub. Discover the Welcome Scroll | Read the scroll fully / Check other rooms first | `innkeeper_study` or role-specific branches |
| `guest_book_parlor` | 3 | Find the guest book with absurd entries | Read entries / Search for clues | `library_chaos` |
| `library_chaos` | 3 | Discover the inn's book collection (mirrors each role's secrets) | **Role-specific choices begin here** | Role-specific branches |
| `innkeeper_study` | 4 | Find the innkeeper's dramatic departure note & video crystal | Play video / Search desk / Read sticky notes | Role-specific explorations |
| `scholar_archive` | 5 | Scholar discovers encrypted forbidden research journals | (Scholar's Secret Quest unlocks here) | Shared progression |
| `rogue_vault` | 5 | Rogue discovers the hidden vault | (Rogue's Secret Quest unlocks here) | Shared progression |
| `mage_ritual_chamber` | 5 | Mage discovers the half-completed spell | (Mage's Secret Quest unlocks here) | Shared progression |
| `conflict_dining_room` | 6 | The inn forces them together; tensions surface | Each role makes choices reflecting their secret quests | `inn_responds_library` / `inn_responds_kitchen` |
| `inn_responds_library` | 7 | The inn rearranges itself based on choices; awkwardness ensues | Confront each other / Continue exploring | `grand_revelation_study` |
| `grand_revelation_study` | 8 | All three secrets are revealed (through gameplay or forced confession) | Apologize & reconcile / Decide what's next | `guest_arrival_foyer` |
| `guest_arrival_foyer` | 9 | A new guest arrives at the inn | Help them / Ask questions / Deliberate | Role-specific guest interactions |
| `final_decision_parlor` | 10 | The three friends gather to decide how to run the inn | **Multiple Ending Choices (Consensus Required)** | `ending_disasters`, `ending_competent`, etc. |

---

### Endings (Require Player Consensus)

1. **"We're Definitely Disasters" Ending:** Chaotic safe house for misfits and people with magical accidents.
2. **"Accidentally Competent" Ending:** They unexpectedly become legitimately good at innkeeping.
3. **"Secret Speakeasy" Ending:** Underground haven for adventurers with secrets and troubled pasts.
4. **"Academic Sanctuary" Ending:** Turn it into a library and research center for scholars and mages.
5. **"Treasure Hunters' Paradise" Ending:** A quest hub where adventurers come for jobs and coin.
6. **"We're Just Winging It" Ending:** Play it by ear and trust the inn to guide them.

Each ending has a unique final scene with role-specific flavor.

---

## Items and Flags

### Items

| Item ID | Name | Purpose | Where Gained | Where Used/Lost |
|---------|------|---------|--------------|-----------------|
| `welcome_scroll` | Welcome Scroll | The innkeeper's cryptic instructions; sets the story in motion | Milestone 2 (Main Hall) | Read during game (flavor); archived in inventory |
| `guest_book` | Guest Book | Contains absurd previous guest entries; establishes inn's history and tone | Milestone 3 (Parlor) | Read/referenced; may be needed for certain choices |
| `innkeeper_note` | Innkeeper's Departure Note | Explains why they left | Milestone 4 (Study) | Referenced throughout |
| `forbidden_journal` | Forbidden Research Journal (Scholar-specific) | Scholar's secret quest item | Milestone 5 (Scholar's Archive) | Used to unlock Scholar's secret choices |
| `treasure_map` | Treasure Map / Vault Key (Rogue-specific) | Hints at the vault; tempts the Rogue | Milestone 5 (Rogue's Vault) | Used to unlock Rogue's secret choices |
| `spell_components` | Spell Components (Mage-specific) | Materials for the risky spell reversal | Milestone 5 (Mage's Ritual Chamber) | Used for Mage's secret quest resolution |
| `brass_key` | Brass Key | Opens locked rooms in the inn (flavor/exploration) | Various scenes | Unlocks optional exploration areas |
| `innkeeper_journal` | Innkeeper's Personal Journal | Reveals innkeeper's backstory and previous catastrophes | Multiple locations | Provides context for endings |

### Flags

| Flag ID | Purpose | Set By | Checked By |
|---------|---------|--------|-----------|
| `quest_1_started` | Tracks "Decipher the Inn's Chaotic History" | Milestone 3 | Progression gates |
| `quest_2_started` | Tracks "Understand Why Innkeeper Left" | Milestone 4 | Progression gates |
| `quest_3_started` | Tracks "Admit Your Ridiculous Past" | Milestone 5 | Progression gates |
| `quest_4_started` | Tracks "Navigate Emotional Minefield" | Milestone 6 | Progression gates |
| `quest_5_started` | Tracks "Convince the Inn" | Milestone 7 | Progression gates |
| `scholar_secret_discovered` | Scholar's secret quest revealed to others | Scholar's choices in Milestone 8 | Final revelation scene |
| `rogue_secret_discovered` | Rogue's secret quest revealed to others | Rogue's choices in Milestone 8 | Final revelation scene |
| `mage_secret_discovered` | Mage's secret quest revealed to others | Mage's choices in Milestone 8 | Final revelation scene |
| `scholar_truth_accepted` | Scholar accepts their past and moves forward | Scholar's choice in Milestone 8 | Affects ending flavor |
| `rogue_truth_accepted` | Rogue chooses loyalty over treasure | Rogue's choice in Milestone 8 | Affects ending flavor |
| `mage_spell_completed` | Mage successfully completes the spell reversal | Mage's choice in Milestone 8 | Affects ending flavor |
| `inn_trusts_players` | The inn accepts them as caretakers (set at Milestone 8) | Accepting the commitment | Gates access to Milestone 9–10 |
| `guest_arrived` | New guest has arrived | Milestone 9 | Triggers final scenes |
| `ending_chosen` | Players have consensus on how to run the inn | Milestone 10 final choice | Determines which ending plays |

---

## Mechanics That Already Work

The story uses these existing features:

- **Scenes:** Each milestone is built from interconnected scenes with up to 25 choices each.
- **Choices with Labels & Hints:** Role-specific choices will be visible to each role in dropdowns (6+ choices per scene).
- **Items:** Players collect items like the scroll, guest book, journals, keys, etc.
- **Flags:** Track quest progress, secret discoveries, and emotional resolutions.
- **Requirements:** Scenes lock choices until certain items are held or flags are set (e.g., can't read the guest book until it's found).
- **Result Text:** Short flavor text appears when a choice is made (e.g., "You carefully open the sealed journal..." or "The Rogue's hands tremble as she touches the vault key").
- **Endings:** Multiple ending scenes based on consensus choice.
- **Solo Play:** A player chooses one role and experiences the full story with their role's perspective.
- **Group Play (2 players):** Both players see choices for their own role plus universal choices; progression requires both to make choices.

---

## New Mechanics Needed

### 1. Synchronized Scene Progression (Required for Group Play)

**What Players See:**
- When a scene presents choices, both players can pick independently.
- A visual indicator shows: "Waiting for [other player]'s choice..." until both have chosen.
- Once both have picked, the scene advances with unified narration reflecting both choices.

**How Writers Use It:**
```yaml
some_scene:
  title: The Mysterious Door
  text: |
    You stand before a heavy oak door. 
    The Scholar wants to examine it carefully.
    The Rogue wants to pick the lock.
    What do you do?
  choices:
    - id: examine_door
      label: Examine the door carefully (Scholar)
      description: Study every detail
      requires: {role: scholar}
      result_text: The Scholar notes ancient runes carved into the frame.
      goto: runes_discovered
    - id: pick_lock
      label: Pick the lock quickly (Rogue)
      description: Use your lockpicking skills
      requires: {role: rogue}
      result_text: The Rogue's picks make quick work of it.
      goto: lock_picked
```

**Rules & Edge Cases:**
- If players pick incompatible choices (Scholar wants to examine, Rogue wants to smash it), the scene branches to handle both:
  - "The Scholar insists on studying it first. The Rogue taps her foot impatiently. After some debate, you [combine outcomes or pick one]."
  - Design principle: Find a way to honor both choices narratively.
- If one player disconnects or becomes inactive, the game can proceed with a timeout (but we said no time limit, so this needs clarification with the dev team).
- Solo players skip this mechanic entirely—they pick once and advance.

**Group Play Impact:**
- Essential for 2-player gameplay. Creates pacing and synchronization.
- Encourages discussion and negotiation when choices conflict.

**Priority:** Must-have for first release.

---

### 2. Role-Specific Quest Tracking (Required)

**What Players See:**
- Quests appear in two categories:
  1. **Shared Quests** (visible to both players): Major milestones everyone works toward.
  2. **Secret/Role-Specific Quests** (visible only to that role): Personal goals that might conflict.
- When a secret quest completes, the other player sees a notification: "[Player Name] completed a secret quest. Its details remain hidden until they choose to reveal it."

**How Writers Use It:**
```yaml
scholar_secret_quest:
  id: restore_research
  title: Restore the Forbidden Research (Scholar only)
  description: The Scholar has found encrypted journals containing research she learned years ago. Should she restore this knowledge or leave it buried?
  objective: Discover and curate the forbidden research
  reward_on_completion: Scholar gains access to unique choices; flag `scholar_truth_accepted` can be set
```

**Rules & Edge Cases:**
- A secret quest is triggered when a role discovers certain items or enters certain scenes.
- Completing a secret quest does NOT automatically reveal it to other players.
- The other players might suspect via hints: "The Scholar has been acting weird around the library" or "The Rogue keeps disappearing to the basement."
- A secret quest can conflict with another player's goal (e.g., Scholar wants to keep the research, Rogue wants to sell it).
- When both players interact with the same object (like the guest book), the narrative acknowledges both roles discovered it.

**Group Play Impact:**
- Critical for creating tension and realistic character conflict.
- Allows players to have personal arcs within the shared story.
- Secret quest completion can unlock unique ending flavors.

**Priority:** Must-have for first release.

---

### 3. Dual Narration (Role-Aware Scene Text)

**What Players See:**
- The same scene can show different context/flavor text based on the player's role.
- Example: In the library, the Scholar sees "The shelves are organized by subject matter, centuries of research..." while the Rogue sees "The shelves have tight spaces between them—perfect for hiding things."

**How Writers Use It:**
```yaml
library_scene:
  title: The Grand Library
  text_scholar: |
    The library stretches impossibly high. Thousands of volumes line the shelves,
    organized by a system that speaks to your academic heart...
  text_rogue: |
    The library is a maze of tall shelves. Your eyes catch on loose floorboards
    and what might be hidden compartments...
  text_mage: |
    The library hums with magic. You can sense wards and preservation spells
    woven throughout the shelves themselves...
```

**Rules & Edge Cases:**
- The base narrative (what happens) is the same for all roles.
- Only the flavor/perspective changes.
- Use this sparingly—don't overdo it or scenes become impossible to write/maintain.
- When players are together in one scene, use unified narration: "The Scholar catalogs the titles while the Rogue checks for hidden compartments. Together, you notice..."

**Group Play Impact:**
- Adds depth and personalization without branching the entire story.
- Makes each role feel special and valued.

**Priority:** Nice-to-have for first release; can be added later.

---

### 4. Notification System for Secret Quest Completion

**What Players See:**
- When one player completes a secret quest, the other player(s) receive a message:
  - "The Rogue has completed a secret quest: 'The Vault's Secret.'"
  - They don't learn what the quest was, but they know *something* happened.
  - Later scenes can reference this: "The Rogue seems relieved about something."

**How Writers Use It:**
- Track when secret quests are marked `complete: true`.
- A scene can check: `if flag(rogue_secret_discovered) then show hint about Rogue's actions`.

**Rules & Edge Cases:**
- Only the completing player's notifications go out.
- The other players don't learn the quest details until:
  1. The completing player chooses to reveal it in dialogue, OR
  2. A later scene forces revelation (like Milestone 8's "Grand Revelation").
- If both players are in the same scene when a quest completes, the narration acknowledges both witnessed it.

**Group Play Impact:**
- Essential for building dramatic tension and mystery.
- Allows players to speculate and build curiosity.

**Priority:** Must-have for first release.

---

### 5. Consensus Ending (Required for Endings)

**What Players See:**
- At the Final Pact scene, both players see all 6 ending choices.
- Each choice is labeled and described.
- Neither player can proceed until both have picked the *same* ending choice.
- If they pick different endings, the game shows: "You can't agree on how to run the inn. Discuss and pick again."

**How Writers Use It:**
```yaml
final_decision_parlor:
  title: The Final Pact
  text: |
    The three of you gather in the parlor. The inn hums softly around you.
    "So... how do we do this?" one of you asks.
    What kind of inn will The Invisible Inn become?
  choices:
    - id: disaster_inn
      label: The Disaster Inn (Safe house for misfits)
      description: A chaotic refuge for people like us
      requires: {both_must_choose_same: true}
      goto: ending_disasters
    - id: competent_inn
      label: The Competent Inn (Professional innkeeping)
```

**Rules & Edge Cases:**
- Both players must explicitly choose the same ending.
- If they choose different endings, show a message: "You and [other player] have different visions. Talk it over."
- Can replay the choice until consensus is reached.
- No fallback or majority-vote system—mutual agreement required.
- Solo players just pick once and get the ending.

**Group Play Impact:**
- Forces genuine player discussion and collaboration.
- Makes the ending feel like a joint decision.

**Priority:** Must-have for first release.

---

### 6. Role Display in UI (Nice-to-Have)

**What Players See:**
- Each player's role is shown in the UI (somewhere visible).
- When a role-specific choice appears, it's labeled: "[Scholar] Examine the door carefully."
- Helps players remember who's doing what in group play.

**Priority:** Nice-to-have for first release; can be added later for UX clarity.

---

## Group Play Notes

### Core Group Play Features (2-Player, Takes Turns)

1. **Simultaneous Choice Making (with wait state):**
   - Both players see the same choices (filtered by their role).
   - Both can pick independently; game waits for both to pick.
   - Once both have picked, scene advances with unified narration.

2. **Shared Inventory:**
   - Items picked up by either player go into a shared inventory.
   - Both players can see `/inventory` and view all shared items.
   - Consuming/using an item removes it for both.

3. **Secret Quests Create Asymmetry:**
   - Scholar's quest: Restore forbidden research.
   - Rogue's quest: Decide what to do with the vault treasure.
   - Mage's quest: Complete the spell reversal.
   - These quests can have conflicting goals (e.g., Scholar wants knowledge preserved, Rogue wants treasure spent).
   - Completing a secret quest triggers a notification; the other player doesn't learn details until revelation.

4. **The Inn's Response to Group Decisions:**
   - The inn reacts to their collective choices.
   - If they're being dishonest with each other, rooms rearrange; doors lead to wrong places.
   - This forces them to address conflicts openly.

5. **Forced Confrontations:**
   - Certain scenes (like Milestone 8) force all three to acknowledge what's been happening.
   - Secret quests are revealed through gameplay or direct conversation.
   - This is where the story resolves the tension.

6. **Final Consensus:**
   - Only one ending can be chosen, and both players must agree.
   - Encourages discussion and compromise.

### Solo Play Adjustments

- A solo player picks one role and experiences the story from that role's perspective.
- Secret quests still exist and are completed normally.
- Since there's no other player, scenes with "waiting for other player" are skipped.
- The final ending choice doesn't require consensus—solo player just picks.
- Narration acknowledges the player is alone: "You stand alone in the inn, knowing you'll have to handle all of this yourself."

---

## Writing Plan

### Who Writes What

- **You (Project Manager):** Oversee structure, milestone goals, and quest arcs. Write key scenes that establish tone and story beats.
- **Claude (AI Assistant):** Help draft scene content, write role-specific flavor text, ensure consistency across scenes.
- **Future Writers (TBD):** Expand scenes, write additional flavor, add more role-specific branches.

### Writing Order (Phase 1: Playable Slice)

Start with a playable 20-30 minute slice to test the mechanics and tone:

1. **Milestone 1–2 (Arrival & First Scenes):**
   - `arrival_storm` – The storm and discovering the inn
   - `foyer_arrival` – Entering and warming up
   - `main_hall` – Central hub with Welcome Scroll

2. **Milestone 3 (Guest Book Discovery):**
   - `guest_book_parlor` – Finding the guest book with absurd entries
   - `library_chaos` – Introduction to the library where role-specific branches begin

3. **Milestone 5 (Secret Quest Discovery):**
   - `scholar_archive` – Scholar finds forbidden research (Scholar's quest unlocks)
   - `rogue_vault` – Rogue finds the vault (Rogue's quest unlocks)
   - `mage_ritual_chamber` – Mage finds the spell chamber (Mage's quest unlocks)

4. **Milestone 8 (Revelation & Resolution):**
   - `grand_revelation_study` – Secrets come to light; quests resolve
   - Brief resolution before Milestone 9

This slice:
- Establishes the tone (quirky, cozy, comedic)
- Introduces all three roles and their secret quests
- Demonstrates synchronized group play
- Shows how the inn responds to choices
- Ends with a satisfying moment before continuing to the final act

### Timeline

- **Week 1:** Sketch full scene list and role-specific branching for Milestones 1–5
- **Week 2:** Write Milestone 1–2 scenes
- **Week 3:** Write Milestone 3 scenes
- **Week 4:** Write Milestone 5 scenes
- **Week 5:** Write Milestone 8 (revelation) and test the playable slice
- **Future Phases:** Complete Milestones 6–10 and add more depth/branches

---

## Open Questions

1. **Time Limits for Group Play:** Should there be a timeout if a player doesn't pick a choice within X minutes? Or wait indefinitely?

2. **Conflicting Choices:** When both players pick incompatible actions in the same scene, should we:
   - Always combine them narratively?
   - Have certain scenes pick one "winner"?
   - Let the earlier choice take precedence?

3. **Solo Play Scaling:** Should solo playthroughs be identical to group play (just one role), or should they have adjusted content/pacing?

4. **Replay Value:** After completing one playthrough, what encourages a second one?
   - Different role choice?
   - Different decisions leading to different endings?
   - Hidden scenes that only unlock on subsequent playthroughs?

5. **Group Size:** The design assumes 2 players. When you expand to 3 players (Scholar, Rogue, Mage all present), how should mechanics change?
   - All three voting on choices?
   - Rotating who picks?
   - Unanimous agreement required for major decisions?

6. **Achievement Tracking:** Beyond quests, should players unlock badges or achievements for reaching certain milestones or making specific choices?

---

## Firm Decisions for Claude Code

These decisions should NOT be revisited without asking the project manager:

- ✅ **Three Roles Only (for Phase 1):** Scholar, Rogue, Mage. More roles can be added later.
- ✅ **No AI-Generated Text:** All scene narration is human-written. No generative AI text in the game.
- ✅ **No Free-Text Input:** Players choose only via buttons/dropdowns. No typing commands beyond `/start`, `/inventory`, `/quit`, `/help`.
- ✅ **Shared Inventory:** Both players share one inventory, not individual ones.
- ✅ **Group Play: 2 Players (Phase 1):** Design for 2-player cooperative play. Expand to 3+ in a later phase.
- ✅ **Synchronized Progression:** Both players must pick a choice before the scene advances.
- ✅ **Consensus Endings:** Both players must choose the same ending to progress.
- ✅ **Secret Quests (10 per role):** Role-specific quests track hidden goals that can conflict.
- ✅ **Tone:** Quirky, cozy, comedic. Light fantasy with no dark elements.
- ✅ **Target Length:** 60 minutes per playthrough.
- ✅ **Multiple Endings:** 6 distinct endings, all achievable through different choices and consensus.
- ✅ **Solo Play:** Supported from Phase 1. One role, same story, no group mechanics.
- ✅ **No Time Limits:** Players can take as long as they want to make choices (no forced timeouts, but this needs clarification if one player goes AFK).

---

**Version:** 1.0  
**Last Updated:** September 27, 2026  
**Status:** Ready for Development
