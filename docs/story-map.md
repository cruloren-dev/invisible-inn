# Story map

> **Generated automatically from the story files. Don't edit this page by hand:** it is
> rebuilt whenever story changes are merged into `main`. To change the story, edit the
> files in `content/stories/` (see `docs/editing-guide.md`).

## The Invisible Inn

15 scenes · 3 items · 3 quests · roles: Scholar, Rogue (coming soon), Mage (coming soon)

**How to read the diagram:** the slanted box is where the story starts, and rounded green boxes are endings. **Dotted arrows with 🔒** need something first (an item, flag or quest); solid arrows don't, though some disappear after they've been used once. "[Scholar]" marks a choice for one role. "↺ N actions here" counts choices that stay in the same scene. Arrow labels are shortened; the tables below have the full text and every condition.

```mermaid
flowchart TD
    s_arrival_storm[/"A Very Rude Storm<br/><small>↺ 2 actions here</small>"/]
    s_foyer_arrival["The Foyer<br/><small>↺ 1 action here</small>"]
    s_kitchen["The Kitchen<br/><small>↺ 2 actions here</small>"]
    s_main_hall["The Main Hall"]
    s_welcome_scroll["The Welcome Scroll"]
    s_guest_book_parlor["The Parlour<br/><small>↺ 1 action here</small>"]
    s_guest_book_entries["The Guest Book<br/><small>↺ 1 action here</small>"]
    s_library_chaos["The Library<br/><small>↺ 1 action here</small>"]
    s_scholar_archive["Restricted Section, Shelf 12-B"]
    s_innkeeper_study["The Innkeeper's Study<br/><small>↺ 1 action here</small>"]
    s_crystal_message["A Message from Madame Thistlewick"]
    s_grand_revelation["The Grand Revelation (Part One)"]
    s_ending_confess(["Put Down"])
    s_ending_secret(["Not Yet"])
    s_ending_unaware(["Nothing to Hide"])
    s_arrival_storm -->|"Knock on the door / Let Sable pick the lock"| s_foyer_arrival
    s_foyer_arrival -->|"Follow the smell of toast"| s_kitchen
    s_foyer_arrival -->|"Head deeper into the inn"| s_main_hall
    s_foyer_arrival --> s_arrival_storm
    s_kitchen --> s_foyer_arrival
    s_main_hall -->|"Read the scroll on the lectern"| s_welcome_scroll
    s_main_hall -->|"Try the door marked PARLOUR"| s_guest_book_parlor
    s_main_hall -->|"Try the humming door"| s_library_chaos
    s_main_hall -.->|"🔒 Try the door marked STAFF ONLY"| s_innkeeper_study
    s_main_hall --> s_foyer_arrival
    s_welcome_scroll --> s_main_hall
    s_guest_book_parlor -->|"Open the guest book"| s_guest_book_entries
    s_guest_book_parlor --> s_main_hall
    s_guest_book_entries -->|"Take the guest book with you / Close the book"| s_guest_book_parlor
    s_library_chaos -.->|"🔒 [Scholar] Follow the shelf mark to the…"| s_scholar_archive
    s_library_chaos --> s_main_hall
    s_scholar_archive -->|"Take the journal / Put it back and walk away. Briskly."| s_library_chaos
    s_innkeeper_study -->|"Tap the crystal twice"| s_crystal_message
    s_innkeeper_study -.->|"🔒 Call everyone together. It's time to ta…"| s_grand_revelation
    s_innkeeper_study --> s_main_hall
    s_crystal_message -->|"Let that sink in"| s_innkeeper_study
    s_grand_revelation -.->|"🔒 Tell them about the journal"| s_ending_confess
    s_grand_revelation -.->|"🔒 Say you've got nothing to confess (you…"| s_ending_secret
    s_grand_revelation -->|"Say you've got nothing to hide"| s_ending_unaware
    classDef ending fill:#3E7C59,color:#fff,stroke:#2b5a40
    classDef start fill:#6B4E9B,color:#fff,stroke:#4d3870
    class s_ending_confess,s_ending_secret,s_ending_unaware ending
    class s_arrival_storm start
```

### Checker warnings

- ⚠ 06_revelation.yaml › grand_revelation: every choice has requirements — players could get stuck here

## Scenes in detail

### A Very Rude Storm

`arrival_storm` in `scenes/01_arrival.yaml` · **start**

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Knock on the door | The Foyer (`foyer_arrival`) | — | — |
| [Scholar] Study the shimmering doorframe | *(stays here)* | Scholar only; not flag `noticed_wards` (disappears once that changes) | sets `noticed_wards` |
| Let Sable pick the lock | The Foyer (`foyer_arrival`) | — | — |
| Suggest you all keep walking | *(stays here)* | not flag `tried_leaving` (disappears once that changes) | sets `tried_leaving` |

### The Foyer

`foyer_arrival` in `scenes/01_arrival.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Warm up by the fire | *(stays here)* | not flag `warmed_up` (disappears once that changes) | sets `warmed_up` |
| Follow the smell of toast | The Kitchen (`kitchen`) | — | — |
| Head deeper into the inn | The Main Hall (`main_hall`) | — | — |
| Step back outside into the storm | A Very Rude Storm (`arrival_storm`) | — | — |

### The Kitchen

`kitchen` in `scenes/01_arrival.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Say something nice to the kettle | *(stays here)* | not flag `kettle_cheered` (disappears once that changes) | sets `kettle_cheered` |
| Eat the toast | *(stays here)* | not flag `ate_toast` (disappears once that changes) | sets `ate_toast` |
| Back to the foyer | The Foyer (`foyer_arrival`) | — | — |

### The Main Hall

`main_hall` in `scenes/02_main_hall.yaml` · own text for: Scholar

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Read the scroll on the lectern | The Welcome Scroll (`welcome_scroll`) | doesn't have Welcome Scroll (disappears once that changes) | ➕ Welcome Scroll |
| Try the door marked PARLOUR | The Parlour (`guest_book_parlor`) | — | — |
| Try the humming door | The Library (`library_chaos`) | — | — |
| Try the door marked STAFF ONLY | The Innkeeper's Study (`innkeeper_study`) | quest *The Inn's Chaotic History* done (greyed out until then) | 📜 starts *The Empty Front Desk* |
| Back to the foyer | The Foyer (`foyer_arrival`) | — | — |

### The Welcome Scroll

`welcome_scroll` in `scenes/02_main_hall.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Roll it up and keep it | The Main Hall (`main_hall`) | — | — |

### The Parlour

`guest_book_parlor` in `scenes/03_parlor.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Open the guest book | The Guest Book (`guest_book_entries`) | — | 📜 starts *The Inn's Chaotic History* |
| Ask Sable what she's looking for | *(stays here)* | not flag `asked_sable` (disappears once that changes) | sets `asked_sable` |
| Back to the main hall | The Main Hall (`main_hall`) | — | — |

### The Guest Book

`guest_book_entries` in `scenes/03_parlor.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| [Scholar] Look closer at the entry in your handwriting | *(stays here)* | Scholar only; not flag `saw_own_entry` (disappears once that changes) | sets `saw_own_entry` |
| Take the guest book with you | The Parlour (`guest_book_parlor`) | doesn't have Guest Book (disappears once that changes) | ➕ Guest Book; ✅ completes *The Inn's Chaotic History* |
| Close the book | The Parlour (`guest_book_parlor`) | — | — |

### The Library

`library_chaos` in `scenes/04_library.yaml` · own text for: Scholar

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| [Scholar] Follow the shelf mark to the Restricted section | Restricted Section, Shelf 12-B (`scholar_archive`) | Scholar only; flag `saw_own_entry`; not flag `visited_archive` (greyed out until then) | sets `visited_archive` |
| Pull Fennick away from his shelf | *(stays here)* | not flag `pulled_fennick` (disappears once that changes) | sets `pulled_fennick` |
| Back to the main hall | The Main Hall (`main_hall`) | — | — |

### Restricted Section, Shelf 12-B

`scholar_archive` in `scenes/04_library.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Take the journal | The Library (`library_chaos`) | — | ➕ Journal in Your Handwriting; 📜 starts *The Forbidden Research* |
| Put it back and walk away. Briskly. | The Library (`library_chaos`) | — | sets `left_journal` |

### The Innkeeper's Study

`innkeeper_study` in `scenes/05_study.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Read the sticky notes | *(stays here)* | not flag `read_notes` (disappears once that changes) | sets `read_notes` |
| Tap the crystal twice | A Message from Madame Thistlewick (`crystal_message`) | quest *The Empty Front Desk* not done (disappears once that changes) | — |
| Call everyone together. It's time to talk. | The Grand Revelation (Part One) (`grand_revelation`) | quest *The Empty Front Desk* done (greyed out until then) | — |
| Back to the main hall | The Main Hall (`main_hall`) | — | — |

### A Message from Madame Thistlewick

`crystal_message` in `scenes/05_study.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Let that sink in | The Innkeeper's Study (`innkeeper_study`) | — | ✅ completes *The Empty Front Desk* |

### The Grand Revelation (Part One)

`grand_revelation` in `scenes/06_revelation.yaml`

| Choice | Leads to | Needs | Does |
|---|---|---|---|
| Tell them about the journal | Put Down (`ending_confess`) | has Journal in Your Handwriting (hidden until then) | sets `scholar_truth_accepted`; ✅ completes *The Forbidden Research* |
| Say you've got nothing to confess (you do) | Not Yet (`ending_secret`) | has Journal in Your Handwriting (hidden until then) | — |
| Say you've got nothing to hide | Nothing to Hide (`ending_unaware`) | doesn't have Journal in Your Handwriting (disappears once that changes) | — |

### Put Down

`ending_confess` in `scenes/06_revelation.yaml` · **ending** · own text for: Scholar


### Not Yet

`ending_secret` in `scenes/06_revelation.yaml` · **ending**


### Nothing to Hide

`ending_unaware` in `scenes/06_revelation.yaml` · **ending**

