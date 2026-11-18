# Living Network | Experimental design v1

**Status:** independent alternative on `design/living-network-v1`. Not a replacement for the current Metro Atlas renderer and not approved for public release.

## The product idea

Turn a year of **source-backed** activity into a network of project journeys. Preserve the familiar 53-week GitHub calendar at the top, then offer a separate project-layer below:

- **Route = repository**, not activity category. The route starts at the project's first observed active week and stops at its last observed active week.
- **Small station = observed activity week** for that repository. Intermediate track is schematic, not an assertion about activity on the days between stops.
- **Large round station = merged PR**; **diamond station = release**. These are generated only from recorded events.
- **Interchange = several projects were active in the same calendar week**. It does **not** imply a dependency, code transfer or a collaboration relationship. At most nine co-activity bridges are drawn to avoid clutter.
- **Milestone passport = four selected, verifiable source entries** with event ID, kind, repository and date. It never invents milestone titles.
- **Replay = move through 53 calendar weeks**. The visible rail network grows chronologically. The browser reveals event IDs and supports filtering by project.

The distinguishing feature is an **interactive replay of a development year**, not decoration over a contribution grid. All three stills remain useful without JavaScript.

## Gallery and provenance

| File | Purpose |
| --- | --- |
| `assets/living-network-showcase.svg` | Midnight presentation, synthetic 108-event density story plus the original ten fixture events |
| `assets/living-network-paper-showcase.svg` | Paper treatment of that exact synthetic story |
| `assets/living-network-snapshot.svg` | Exactly ten fixture source events; no additional data |
| `assets/living-network-showcase.html` | Self-contained interactive replay and repository focus for the synthetic story |
| `assets/living-network-snapshot.html` | Self-contained replay of the faithful sparse fixture |

**All source data is illustrative, not the owner's actual GitHub contributions.** In the source demo, `demo_story()` adds deterministic events on purpose, but it raises `ValueError` for `source="github"` and never alters the underlying input. It is strictly forbidden to use that function for public or private real-account snapshots.

## Local commands

```powershell
py -3 -m pip install -e .
py -3 -m unittest discover -s tests -v

# Faithful ten-event fixture
py -3 -m open_source_metro.living_network --input examples/demo-activity.json --output output/living-fixture

# Explicitly fictional showcase
py -3 -m open_source_metro.living_network --input examples/demo-activity.json --output output/living-showcase --showcase

# Alternative theme
py -3 -m open_source_metro.living_network --input examples/demo-activity.json --output output/living-paper --showcase --theme paper

Start-Process .\output\living-showcase\living-network-showcase.html
```

The interactive file works offline and does not contact GitHub, inject external JavaScript, use cookies, access local files or require an API key. Open it in a local browser after generating it. GitHub's code viewer **does not execute** HTML and an embedded README SVG **is not an interactive application**.

## Engineering design

`src/open_source_metro/living_network.py` builds on `validation.normalise()` from the existing package. It introduces no new runtime dependencies and does not modify `renderer.py` or the stable console command.

1. `build_plan()` validates v1 JSON, retains events in the 53-week calendar window up to the exact snapshot timestamp, selects at most five event-active repositories and retains up to 240 source events. A cut through a busy day omits the whole oldest day. All dropped events/repositories are disclosed.
2. `render_svg()` uses one deterministic time coordinate for both the calendar and each repository line. A week stop is drawn only when the selected repository has one or more source events that week. Milestones derive strictly from `pr_merged` or `release`.
3. `browser_html()` embeds a validated SVG and a JSON event ledger. Input text becomes plain DOM text; source IDs in JSON are escaped so they cannot close `<script>` tags. The Content Security Policy blocks remote requests.
4. Browser playback: Play/Pause, Restart, 1×/2×/4×, week scrubber, focus buttons and a source-event list. No autoplay, even when the user has not enabled reduced motion. Keyboard focus is visible.
5. `generate()` writes an SVG and a self-contained HTML file for either the input fixture or the explicit `--showcase` mode.

## Visual rules and accessibility

- Calendar remains recognisable and unmodified as a 53 × 7 date lattice.
- Repository colour is consistent across route, stations and passport ticket.
- Route lengths represent the span between *first and last observed source week*, not a count of contributions or continuous daily activity.
- Active weeks are identifiable by circles; merges/releases are bigger and marked inside.
- All states have accessible titles and descriptive SVG metadata; project filtering works without colour alone.
- Browser preview uses live text updates, labelled controls and horizontal scrolling at narrow widths.
- Static SVG is the GitHub-compatible fallback. Browser replay has no hosted deployment yet.

## Review findings and known limits

- At small GitHub README sizes the entire 1460 × 938 artwork becomes hard to read. A **compact profile preset** should be built before release, separate from the detailed storyboard.
- Only five repositories are featured; hidden repositories and excluded events are disclosed but no interactive discovery of all repositories exists.
- Public GitHub data collector is **not implemented**. Source event units do not equal GitHub's authoritative contribution totals.
- Calendar density and milestone names depend on the supplied snapshot, with no invented intermediate events in real mode.
- Interchange bridges are limited to nine for legibility and mean only contemporaneous activity, not project relationships.
- The demo's 108 invented events deliberately create overlapping project narratives. They must never be presented as genuine profile history.
- No live animation/GIF is embedded in a GitHub README. Interactive playback is local, through HTML.

## Next review questions

1. Is the **network of repository journeys** more meaningful than routes coloured by event type?
2. Are the milestone passport cards valuable, or should a compact profile embed prioritise just a few headline stations?
3. Does the chronological replay make the concept memorable enough to warrant a dedicated public tool?
4. After owner design feedback, should the team build a compact GitHub profile preset or explore a *genuinely different* graphic metaphor?

This design intentionally remains a **draft PR** until the owner selects a direction. The previous Metro Atlas and its verified CI remain intact on `master`.
