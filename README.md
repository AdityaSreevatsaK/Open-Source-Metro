# Open Source Metro

## Official GitHub contribution calendar + source-backed project routes

The calendar and the project network are **different, explicitly labelled data layers**. When a read-only `GITHUB_TOKEN` is available, we query GitHub GraphQL for **profile-visible daily contribution totals** and render those in the familiar 53-week squares. The five metro routes below still represent only **independently observed public repository events**. Neither the route count nor the source-event ledger is presented as a breakdown of the calendar total.

This fixes the earlier near-empty real-account graph: GitHub's own API returned **1,883 profile-visible contributions across 99 active days** for `AdityaSreevatsaK` on 18 November 2026, while the older public repository collector observed only a few days. This is a snapshot, not a permanent account statistic. Your profile's visibility settings may include anonymous private/restricted contribution counts.

**Generate without editing your profile:** Actions → **Generate public Metro profile (manual)** → **Run workflow**. The downloadable archive contains both SVGs and a source snapshot with the two separately identified datasets. The workflow uses the repository's read-only GitHub Actions token and writes no profile files.

For offline testing with a synthetic snapshot, no token is required. Without a token during live local generation, the CLI falls back to the incomplete public-repository event calendar and labels that limitation clearly.

[Technical setup, GraphQL scope and provenance](docs/YEAR_HISTORY_AND_SELF_SERVICE.md).

---

> **Improved real-data interpretation:** The renderer now preserves all observed events, even in dense days, rather than dropping the oldest activity at 240 events. The 53-week overview reports **how many weeks actually have observations** and the first/last observed dates. Public activity in newly created repositories can legitimately cover only a few days, so a mostly blank full-year chart does not mean all GitHub contributions were zero. The default automatic public-repository selection now balances recent and older projects; use `--repos` to specify other public repositories.

## Self-service public profile generator | Year-scale repository history

**New:** Generate a compact 53-week Metro banner and a separate 16-week portrait card for a public GitHub account. Unlike the older 30-day Events API sampler, the new collector reads **source-backed history** from selected public repositories. It records exactly what it saw and documents all coverage gaps.

```powershell
py -3 -m pip install -e .

# Public source-backed profile for a GitHub username
py -3 -m open_source_metro.profile_cli --username AdityaSreevatsaK --output output/my-profile --layout both

# Fully offline, reproducible sample (fictional fixture only)
py -3 -m open_source_metro.profile_cli --input examples/demo-activity.json --output output/demo-profile --layout both
```

Output: `source-snapshot.json`, `profile-compact.svg`, `profile-mobile.svg` and `README_SNIPPET.md`. Use `--featured owner/repo` to pick an included repository, `--repos owner/repo,owner/other` to choose the **live collection scope**, and `--theme paper` for the lighter design.

**Important:** This is **not** GitHub's complete contributions calendar. Commits are from the current default branch; other repos, branch histories, reviews and private contributions may be absent. The source manifest describes the precise window and omissions. Blank cells are *unobserved*, not proven zero contributions.

**No-code option:** From the repository's **Actions** tab, select **Generate public Metro profile (manual)** → **Run workflow**, enter a public username, then download the `open-source-metro-public-profile` artifact. It contains both requested SVGs, the source and coverage manifest, and suggested README embed text. Artifacts expire after **7 days**; no changes are pushed to any profile.

[Full collection and self-service guide](docs/YEAR_HISTORY_AND_SELF_SERVICE.md). No real-account data is bundled, no profile repository is modified and no paid service is required.

---

## New experimental capabilities | Mobile + public-event snapshots

A **dedicated 460 × 808 mobile portrait card** is now available. It deliberately shows the **most recent 16 weeks**, rather than crushing the annual 53-week chart into an unreadable phone width. Its stops and repository routes are based only on observed source events, with a separate midnight and paper theme. [Mobile architecture and examples](docs/MOBILE_PROFILE.md).

```powershell
py -3 -m open_source_metro.mobile_profile --input examples/demo-activity.json --output output/mobile-showcase.svg --showcase
py -3 -m open_source_metro.mobile_profile --input examples/demo-activity.json --output output/mobile-fixture.svg
```



### Portrait mobile gallery (synthetic illustration)

![Dedicated 16-week portrait Open Source Metro with five repository journeys and event-backed stops; synthetic demonstration only.](assets/living-mobile-showcase.svg)

<details>
<summary>Paper theme and original fixture-only mobile version</summary>

![Warm paper-coloured 16-week portrait network, using explicitly synthetic demonstration events.](assets/living-mobile-paper.svg)

![Portrait network built from the ten original synthetic fixture events only, without any additional illustrative events.](assets/living-mobile-fixture.svg)

</details>

The initial **public GitHub Events API adapter** supports recent source-backed, username-specific events without a token, but is **not a complete GitHub contribution history**. It accesses only public events, at most 300 events from the previous 30 days, and skips pushes without explicit commit lists rather than inventing counts. All results are written only to local `output/`, never checked in as the owner's activity.

```powershell
py -3 -m open_source_metro.public_events AdityaSreevatsaK --output output/public-snapshot.json --compact-svg output/public-compact.svg --mobile-svg output/public-mobile.svg
```

[Collector data/coverage contract](docs/PUBLIC_EVENTS_COLLECTOR.md). **Neither output has been installed on the owner's live GitHub profile.**

---
## Living Network | Compact GitHub-profile edition

**Project routes tell the story.** Each coloured line is a repository, with stops only at recorded active weeks. Rings indicate merged PRs; diamonds indicate releases. The upper layer retains the familiar 53-week GitHub-style contribution calendar.

**Chronological compact replay, synthetic demonstration only:**

![Compact Open Source Metro replay of a 53-week contribution-style calendar with five repository journeys and source-observed stations appearing over time. All activity is explicitly fictional demo data.](assets/living-compact-replay.gif)

The replay shows train markers at the **latest recorded stop**, never a made-up contribution. The final completed network stays visible for 2.2 seconds. A still-image fallback is available:

![Static compact midnight Living Network profile design with a recognisable contribution grid and five repository journeys. Clearly labelled synthetic data.](assets/living-compact-showcase.svg)

<details>
<summary>Compact alternatives: paper design and faithful ten-event fixture</summary>

![Compact paper-coloured Living Network with identical, explicitly fictional demonstration data.](assets/living-compact-paper.svg)

![Compact Living Network using only the ten original synthetic fixture records, without added illustration events.](assets/living-compact-fixture.svg)

</details>

**The showcase is not your actual GitHub activity.** It includes 108 expressly invented events, while the fixture-only view contains only the original ten example events. These are source-shaped **illustrations**, not GitHub's official contribution totals.

See [compact design specification, generation commands and provenance rules](docs/COMPACT_LIVING_NETWORK.md).

### Full Living Network | Detailed, interactive version

The complete storyboard and its interactive browser event register remain available alongside the compact edition.

<details>
<summary>Watch the original full-size annual replay</summary>

![Full-size animated Open Source Metro project network growing chronologically over 53 weeks, from synthetic example events.](assets/living-network-replay.gif)

</details>

**The calendar now tells a story instead of just wearing coloured lines.** In this alternative, **each route represents a repository**. Small stops are source-observed active weeks; distinct rings highlight PR merges and releases. A milestone passport shows exact source event IDs and dates. The **interactive replay** lets you travel through 53 weeks, focus on a repository and inspect source events.

![Living Network midnight: 53-week contribution calendar, five repository-specific journeys and milestone passport, explicitly synthetic showcase.](assets/living-network-showcase.svg)

<details>
<summary>Compare paper treatment and faithful sparse fixture</summary>

![Living Network parchment presentation using identical, explicitly invented demonstration data.](assets/living-network-paper-showcase.svg)

![Living Network sparse preview containing exactly the original ten synthetic fixture events.](assets/living-network-snapshot.svg)

</details>

**These gallery assets are fictional samples, not your real GitHub activity.** The showcase adds 108 clearly marked, deliberately invented event records to the ten-event demo. The fixture version adds none. There is no live GitHub collector.

**Try the working, offline browser replay:**

```powershell
py -3 -m pip install -e .
py -3 -m open_source_metro.living_network --input examples/demo-activity.json --output output/living --showcase
Start-Process .\output\living\living-network-showcase.html
```

Use the Play/Pause controls, week scrubber, speed selector and repo filters to explore observed events. The checked-in [interactive showcase HTML](assets/living-network-showcase.html) can also be downloaded and opened locally. GitHub itself does not run HTML from README embeds.

**Optional GIF export** (not required for the regular Python renderer):

```powershell
py -3 -m pip install -e ".[animation]"
py -3 tools/render_replay_gif.py --input examples/demo-activity.json --output output/living-network-replay.gif --showcase --frames 24 --width 760 --duration-ms 180
```

**Read:** [Living Network design, architecture, semantic rules and limitations](docs/LIVING_NETWORK_EXPERIMENT.md). This is a **separate design experiment on `design/living-network-v1`**, not a replacement for the current production baseline or an approved public release.

---

**A GitHub-style contribution calendar that doubles as a metro map.** Each square represents a date, the five parallel lines represent distinct public-event categories, and numbered terminals identify featured repositories.

> **Project status: experimental / pre-alpha.** This is a reproducible offline visualisation prototype, not an official GitHub contribution graph or a completed public-data collector. The design is still under review.

## Design gallery

### Midnight Metro (explicitly synthetic density showcase)

![Open Source Metro midnight preview. A GitHub-style 53-week calendar with five straight, colour-coded metro services and numbered repository stops. Synthetic demonstration only.](assets/atlas-midnight-showcase.svg)

### Parchment Metro (same synthetic showcase)

![Open Source Metro vintage parchment preview with straight metro services and the familiar contribution calendar. Synthetic demonstration only.](assets/atlas-parchment-showcase.svg)

### Original fixture without added activity

![Open Source Metro generated from the original ten synthetic example events only, without any invented additional activity.](assets/atlas-midnight-fixture.svg)

The two showcase previews add **188 deliberately synthetic events** to make the layout easier to evaluate. The fixture-only preview shows **exactly ten** source-example events. **None of these charts represents the repository owner's actual GitHub contributions.**

## Understand the map

| Visual element | Meaning | Important limitation |
| --- | --- | --- |
| 53 × 7 squares | Sunday-to-Saturday calendar aligned to the generated snapshot | Blank squares mean *no event in the supplied snapshot*, not necessarily zero GitHub contributions |
| Green intensity | Source-backed event units on a day | Unlike event types are **not** all commits |
| Five straight lines | CODE: commits; PROPOSE: opened PRs; MERGE: merged PRs; DISCUSS: opened issues; SHIP: releases | Rails are schematic lanes, **not** evidence of journeys between repositories |
| Coloured roundels | Weeks with recorded events in that service | Rails between stops do not imply activity on unmarked dates |
| Numbered terminals | Selected repositories anchored to observed dates | Only five repositories are featured; omissions must be disclosed |

## Quick start on Windows

Requires **Python 3.11+**, Git and no API token. The renderer itself uses the Python standard library.

```powershell
git clone https://github.com/AdityaSreevatsaK/Open-Source-Metro.git
cd Open-Source-Metro
py -3 -m pip install -e .
py -3 -m open_source_metro --input examples/demo-activity.json --output output
py -3 -m unittest discover -s tests -v
```

Use `python` instead of `py -3` on Linux/macOS. Outputs are three deterministic SVGs in `output/`. To try a public, **already normalised** v1 snapshot, supply its JSON path as `--input`. The renderer does **not** fetch GitHub data.

### Repository layout

```text
src/open_source_metro/   Standalone validator and deterministic SVG renderer
examples/                Labelled, synthetic v1 input snapshot
assets/                  Reviewed, reproducible static SVG previews
tests/                   Offline unit, safety, provenance and regression tests
docs/                    Architecture, data contract, design and release guidance
.github/workflows/       Token-free CI on Windows and Linux
AGENTS.md                Required reading and working agreement for AI agents
CONTRIBUTING.md          Human contributor workflow
SECURITY.md              Responsible disclosure and data-handling expectations
```

## Development, agents and public release

Start with [AGENTS.md](AGENTS.md), then [Architecture](docs/ARCHITECTURE.md), [Data contract](docs/DATA_CONTRACT.md), [Design principles](docs/DESIGN_PRINCIPLES.md), [Development guide](docs/DEVELOPMENT.md), [Agent handover](docs/AGENT_HANDOVER.md), and [Release checklist](docs/RELEASE_CHECKLIST.md).

All work should be reviewed and tested before claiming production readiness. **No real-account data is bundled, no paid API is required and no GitHub profile is modified.** Two independent collectors exist: a 30-day public Events API sampler and a bounded year-scale public repository-history adapter. **Neither equals GitHub's official complete contribution calendar.**

### Origin and licensing

Extracted as a standalone project from the Open Source Metro experiment in [GitHub Activity Studio](https://github.com/AdityaSreevatsaK/GitHub-Activity-Studio/tree/concept/open-source-metro). Obsolete alternate renderers and unrelated concepts were intentionally not copied.

MIT licence. No release has been published and the current artwork is a design candidate, not the final visual identity.
