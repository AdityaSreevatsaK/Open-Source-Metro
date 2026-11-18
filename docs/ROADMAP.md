# Roadmap and prioritised engineering backlog

This roadmap separates **design acceptance** from **engineering correctness**. It is deliberately not a promise that the current picture is ready to publish.

## Phase 0: Standalone migration (completed baseline)

- [x] New, self-contained Python package.
- [x] Canonical v1 data validator extracted.
- [x] Retain active straight-rail SVG renderer.
- [x] Preserve original synthetic 10-event fixture.
- [x] Preserve three reproducible SVG previews with honest demo labels.
- [x] Add initial regression tests and no-token CI workflow.
- [x] Document architecture and agent operating conventions.
- [ ] Check GitHub-hosted CI outcome on latest commit (pending verification).

## Phase 1: Design acceptance (highest priority)

**Goal:** visual attractive enough to represent the project, comprehensible to a first-time viewer.

- [ ] Prototype **three materially different, calendar-first** design treatments within this repo (not five new competing projects).
- [ ] Ensure each demonstrates the *same* data semantics; do not invent “journeys” or real-account contributions.
- [ ] Reduce label overload and visually clarify weekly stops versus repository terminals.
- [ ] Prototype compact, desktop and narrow-mobile compositions. Preserve a full 53×7 calendar.
- [ ] Provide side-by-side PNG screenshots and the export SVGs; choose one with owner.
- [ ] Make colour-independent event-type identification clear.
- [ ] Include a rigorous empty/sparse/dense comparison, not just synthetic busy scenes.
- [ ] Improve contrast, legibility and hierarchy without falling back to decorative squiggles.

**Exit:** owner explicitly chooses a treatment; user testing confirms comprehension, then focus on packaging.

## Phase 2: Robust user experience

- [ ] Add \`--mode snapshot\` to generate only selected themes from arbitrary \`source="github"\` without synthesising anything.
- [ ] Provide \`--theme midnight|parchment\` and \`--format\` or named export presets; preserve existing CLI compatibility where possible.
- [ ] Create an optional browser preview with hover, focus, event detail and zoom while keeping static SVG viable.
- [ ] Add screenshot-based image regression and golden-file size tests.
- [ ] Limit memory usage, file sizes and pathological source lists.
- [ ] Improve colour-blind accessibility, keyboard access and reduced-motion behaviour.

**Exit:** complete test suite, reproducible artefacts and legible mobile output.

## Phase 3: Public GitHub data integration (separate review required)

- [ ] Write a dedicated collector design proposal with source endpoint coverage.
- [ ] Distinguish public event coverage from official contribution counting.
- [ ] Support \`GITHUB_TOKEN\` only as optional **read-only** configuration, never bundled.
- [ ] Enforce public-only collection by default; no silently included private repositories.
- [ ] Implement incremental pagination, caching, rate limit recovery, safe timeouts and retries.
- [ ] Preserve a manifest of source URLs, query timestamp, coverage limits and omissions.
- [ ] Add mock-based tests and run CI without network or paid API.

**Exit:** provenance audit; no inflated or invented contributions; owner approval.

## Phase 4: Open-source readiness

- [ ] Verify GitHub README static SVG rendering in both GitHub UI themes.
- [ ] Complete security and accessibility audits.
- [ ] Verify Windows/Linux CI and a clean-clone installation.
- [ ] Finalise public API, error messages, license acknowledgement, docs, examples and contribution guidelines.
- [ ] Create a changelog and release candidate; do not tag stable v1 until explicitly approved.
- [ ] Optionally add a GitHub Action for users to generate their own profile asset, with bounded permissions and opt-in only.

## Success criteria

1. **Understandability:** viewer understands dates, lines and stations without a long text explanation.
2. **Trustworthiness:** real-data mode neither invents nor exaggerates events.
3. **Adoptability:** Python 3.11+, Windows, no WSL, no secrets/paid CI, easy clone/run.
4. **Maintainability:** small modular renderer with testable semantics and deterministic output.
5. **Aesthetics:** memorable, high-quality visual that the owner approves after seeing rendered examples.

## Explicit non-goals at present

- Rendering someone else's private GitHub activity.
- Claiming the chart equals GitHub's official contribution totals.
- A hosted multi-user dashboard or paid account service.
- Artificial activity inflation on public snapshots.
- A reskinned snake animation.
- Developing GitHub Activity Studio's other concepts.


## November 2026 progress: Living Network and source integration

- [x] Living Network PR #1 merged. Repository journeys, interactive 53-week replay, compact 53-week SVG/GIF now on master.
- [x] Dedicated **16-week portrait** renderer, source-backed with distinct midnight/paper themes, proposed in PR #2.
- [x] Bounded **public-only recent Events API** adapter with mock-only tests, proposed in PR #2.
- [ ] Evaluate actual mobile portrait artwork on a 320–420px viewport and refine typography.
- [ ] Implement a **separately source-validated year-scale collector**. The public Events API's 30-day/300-event bound does not supply full-year contribution coverage, and current PushEvent payloads do not provide complete commit counts.
- [ ] Add user-selectable featured repositories, meaningful linked milestones and read-only hosted browser preview.
- [ ] Owner sign-off before an installation on a live GitHub profile or release.
