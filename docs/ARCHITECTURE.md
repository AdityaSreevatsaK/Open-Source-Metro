# Architecture | Open Source Metro

## Intent and current stage

Open Source Metro is a pure-Python **offline event visualisation engine**. It accepts a versioned, already normalised public-event snapshot and generates three standalone SVG assets. The repository intentionally contains **no GitHub authentication, live API client, database, hosted backend, runtime JavaScript, paid model, telemetry or automated profile-write integration**.

The current implementation is a **pre-alpha renderer**. It was extracted from GitHub Activity Studio without importing the legacy map generators.

## System boundary

\`\`\`text
                         Trusted local / user-supplied file
                                     |
                   examples/demo-activity.json or custom v1 JSON
                                     |
                                     v
                  +-------------------------------+
                  | validation.normalise(snapshot)|
                  |  * schema + timestamp checks  |
                  |  * repository and event IDs   |
                  |  * URL/Unicode restrictions    |
                  |  * deterministic dedup/order   |
                  +-------------------------------+
                                     |
                  normalised events/repositories (in memory)
                                     |
                                     v
                  +------------------------------------+
                  | renderer.render(data, theme)       |
                  |  * select 53-week date window      |
                  |  * feature five source routes      |
                  |  * build 371-cell Sun-Sat lattice   |
                  |  * compute straight service tracks |
                  |  * place week stops and terminals  |
                  |  * generate accessible SVG/XML     |
                  +------------------------------------+
                                     |
                            static SVG export
                                     |
                              GitHub README
\`\`\`

The CLI also offers a **demo-only** \`expand_showcase()\` function that adds seeded, explicitly invented events to display a higher-density design. It must never be invoked for \`source="github"\`.

## Modules and responsibilities

### \`src/open_source_metro/validation.py\`

Public functions:
- \`utc_timestamp(value)\`: reject non-UTC and missing-zone times.
- \`safe_label(value, limit)\`: reject control characters, illegal XML code points, bidi overrides and excessive lengths.
- \`safe_url(value)\`: allow only safe GitHub HTTPS links; others become \`None\`.
- \`normalise(source)\`: validate the entire v1 snapshot; reject unknown repository references and conflicting duplicate IDs; sort events by UTC timestamp and ID.

Normalised keys: \`generated\` (UTC datetime), \`source\`, \`user\`, \`repos\`, \`events\`, \`repo_total\`, \`event_total\`. Each event has \`id\`, \`kind\`, \`repo\`, \`date\`, \`count\`, \`url\`.

Do **not** bypass this layer with ad hoc parsing of raw JSON.

### \`src/open_source_metro/renderer.py\`

- \`SERVICE\`: five source-event kinds and distinct service names/colours.
- \`COLORS\`: midnight and parchment themes.
- \`metro_track(events, positions, index)\`: returns a straight horizontal SVG track and an observed-active-week stop list for one service.
- \`render(data, theme="midnight")\`: validates data and emits a standalone SVG string.
- \`expand_showcase(snapshot)\`: fixed-seed, artificial density illustration; demo input only.
- \`generate(fixture, output)\`: exports one original fixture and two illustration variants.
- \`main()\`: \`--input\` and \`--output\` CLI parameters.

The layout is approximately **1440 × 602 SVG units**. \`GX\`, \`GY\`, \`GAP\` and \`CELL\` control chart geometry. Dates are Sunday-first for a fixed 53-week window ending at \`generated_at\`, not at the host computer's current clock time.

### \`src/open_source_metro/__main__.py\` and packaging

\`python -m open_source_metro\` and the installed \`open-source-metro\` console command both reach \`renderer.main()\`.

\`pyproject.toml\` defines a src-layout Python package. The runtime renderer uses only the standard library.

## Core visual semantics

**Calendar:** every cell is one UTC day. Intensity reflects units in the supplied snapshot. The blank state means “not observed”, not an authoritative statement about total GitHub contributions.

**Metro services:** five horizontal lanes occupy grid gutters. A coloured stop represents a week containing at least one event of that particular kind. The line between stops is **schematic transport styling**, not a claim that daily contributions occurred throughout the week or that a train visited unrelated repositories.

**Terminals:** one prominent numbered marker per featured repository, attached to the date of a selected meaningful source event. The station index is explained in the directory below the chart. The current model features up to five repositories.

**Event selection:** all observed in-window events from the supplied source are retained in day-square totals. At most five active repositories receive visible routes, selected by observed activity. Other collected repository events still contribute to the annual calendar. Only events outside the 53-week calendar or after the snapshot cut-off are excluded. No arbitrary 240-event cap or boundary-day deletion remains. The first/last observed date and active-week coverage are disclosed for real data.

**Synthetic showcases:** use \`random.Random(9407)\`, add 188 illustration-only source-shaped events, and visibly state these are invented. The original fixture view is never expanded.

## Data integrity and security assumptions

Source rows are **untrusted**. User-controlled text is XML-escaped in labels and \`title\` metadata. Validate and limit all identifiers, URLs, dates, numeric counts, repository references and duplicate IDs. Do not render raw user-supplied HTML. Do not include external CSS/JS, fonts, authentication cookies or tokens in generated SVGs.

**Threat model:** malicious snapshot text, invalid Unicode, confusing event semantics, deceptive repository ownership, real/private-data leakage, malformed SVG, unsafe links and generated-output drift. Keep the validator independent from the layout.

## Determinism contract

For a fixed snapshot, Python version and theme, generated SVG bytes should remain stable. No \`datetime.now()\`, unseeded random values, environment-sensitive fonts embedded in SVG, unordered iteration affecting display, implicit timezones or live API lookups.

The CI workflow regenerates all three SVGs and compares bytes against \`assets/\`. Any changed output should be intentional, reviewed visually and committed with corresponding test updates.

## Extension boundaries

- **Future collector:** must be an independent adapter, not embedded in \`render()\`; require separate coverage/privacy/design approval. GitHub REST events are not equivalent to the complete contribution calendar.
- **Future browser preview:** read-only, accessible, keyboard usable, reduced-motion aware and independent of remote services for the demo.
- **Future additional layouts:** should retain the shared semantic model, deterministic SVG generation and readable calendar, with visual acceptance before major rearrangement.
- **Future packaging:** no runtime dependency explosion; ensure Windows without WSL still works.

## Existing technical debt / known limits

- The current wide image is hard to interpret at narrow GitHub mobile widths.
- Station choice and route representation are a design candidate, not final approval.
- Only five repositories are featured. Richer multi-repository interaction is not yet implemented.
- No live GitHub collector exists. Current public-event shape does **not** prove complete contribution totals.
- No screenshot-based, pixel-level visual regression system exists yet.
- CI must be checked after GitHub accepts the workflow in the new repository.
- Current static SVGs are intended for GitHub READMEs; animation is not required.


## Two independent real-account data sources

```text
             GitHub GraphQL profile-visible contributions
                 (optional, authorised read-only POST)
                                |
                       _calendar.days[]
                                |
                                v
                  53-week / 16-week DAY SQUARES
                                ^
                                |
                  v1 source 'activity' only when GraphQL absent

          GitHub REST public repository histories (bounded)
                                |
                         v1 activity[]
                                |
                                v
                 up to five featured project ROUTES
```

The two layers are intentionally **not added together**. GraphQL day counts are GitHub profile-visible totals, which may include restricted anonymous activity according to public profile settings. REST public repository history provides verifiable repository/event IDs, but is incomplete. An unobserved REST event is not proof of a zero GitHub day. The official contribution-calendar adapter is in `contribution_calendar.py`, with a fixed GraphQL endpoint and strict validation. Snapshots without `_calendar` remain supported and will use source-ledger counts with an explicit partial-coverage label.
