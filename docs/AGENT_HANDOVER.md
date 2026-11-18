# AI agent handover | Open Source Metro

**Canonical repository:** https://github.com/AdityaSreevatsaK/Open-Source-Metro  
**Default branch:** \`master\`  
**Stage:** standalone prototype, pre-alpha, visual design not signed off  
**Last architectural migration:** 18 November 2026  
**Primary environments:** Windows PowerShell, Python 3.11+, PyCharm. Also tested conceptually for Linux via CI configuration.

This document is a **working technical handover**, not an instruction to assume the existing implementation is production-ready.

## 1. Origin and decisions

The project began inside \`AdityaSreevatsaK/GitHub-Activity-Studio\` as one of five competing visual concepts. The user then directed that **Open Source Metro must develop independently**, with its own repository and eventual public usability.

Relevant owner feedback:
1. A disconnected metro map was not recognisable as the GitHub contribution chart.
2. The calendar must form the **central structure** of the visual.
3. Subsequent “fancy” iterations with winding tracks were considered a bunch of confusing squiggly lines.
4. The current baseline therefore uses **five straight, parallel lines**, one per event type.
5. The design is still not approved as final. Do not mistake the existence of automated tests for aesthetic acceptance.
6. The user asked to migrate what is required into this standalone repository and provide **very detailed instructions for AI agents**.
7. Work on other GitHub Activity Studio concepts is expressly out of scope.

## 2. What was migrated, and why

- \`src/open_source_metro/renderer.py\` from active \`metro_atlas.py\`: currently supported static SVG renderer.
- \`src/open_source_metro/validation.py\`: extracted v1 source validation and deduplication previously buried in a legacy visual renderer.
- \`src/open_source_metro/__init__.py\` and \`__main__.py\`: stable package/import/CLI entry points.
- \`examples/demo-activity.json\`: original synthetic v1 fixture, five repos and ten source events.
- \`assets/atlas-midnight-fixture.svg\`: faithfully displays original ten demo events.
- \`assets/atlas-midnight-showcase.svg\`: includes 188 clearly invented illustration-only events.
- \`assets/atlas-parchment-showcase.svg\`: same illustration density in a different theme.
- \`tests/test_renderer.py\`: 14 original Atlas behavioural/visual-structure/export tests, adapted for standalone paths.
- \`tests/test_validation.py\`: nine additional source-security, provenance and deduplication tests.
- \`pyproject.toml\`, \`.gitignore\`, \`.github/workflows/ci.yml\`: packaging, hygiene and reproducibility.

**Intentionally excluded:** old \`metro.py\`, old \`calendar_metro.py\` artwork, prior unrelated browser preview, obsolete exported SVGs and old tests that require those removed designs. Their continued presence would create false “multiple official renderer” ambiguity.

The old GitHub Activity Studio branch and PR are **historical references**, not the source of truth. Do not alter them as part of standalone development unless explicitly asked.

## 3. Verified local baseline

The standalone migration was exercised locally with:
\`\`\`powershell
python -m unittest discover -s tests -v
python -m open_source_metro --input examples/demo-activity.json --output output
\`\`\`
**23 tests passed locally**, and generated output was byte-identical to all three committed SVG examples. CI checks need separate verification after workflow activation; do not assume a workflow file means it has run successfully.

## 4. Current processing semantics

- **Input:** already assembled, public-safe JSON v1, not raw GitHub API responses.
- **Validation:** strict schema, safe strings/URLs, UTC dates, duplicate protection, no bogus event kinds.
- **Rendering:** 53 weeks × 7 days, activity-unit intensity, five semantic straight transit lanes, observed-week roundels and five featured repository terminals.
- **Labels:** synthetic showcase, synthetic fixture or incomplete public event snapshot.
- **Output:** wide, static standalone SVG suitable as a GitHub README image, with provenance and omissions disclosed.
- **Generation:** \`generate()\` creates both real fixture and synthetic showcase renders; it is therefore **demo-only** in practice. A single real public snapshot is renderable via \`render(data, theme)\`.

## 5. Current unsolved problems and risks

### P0 for visual/product acceptance
- Even with straight lines the visual may remain too diagrammatic or low-impact. Improve the *information architecture* and aesthetics with actual rendered mock-ups.
- A very wide, detailed SVG can be unreadable at GitHub mobile widths. Explore a compact profile variant and a large detail view without misleading data.
- Station/terminal relationships are not yet intuitive enough for an unfamiliar viewer.
- Some colour-only distinctions might not be sufficiently accessible without reading the legend.

### P1 for engineering/public use
- Add an explicit CLI mode for rendering **one actual public snapshot** without attempting the synthetic showcase.
- Introduce a clear “complete/partial/unknown coverage” data provenance extension only after versioned contract design.
- Establish pixel-based screenshot regression and real GitHub README embedding checks.
- Confirm GitHub Actions on both Windows and Linux; check if new repo needs Actions enabled.
- Add code quality checks, tests for large/malicious inputs and SVG size limits.

### P2 for real integration
- Design a public-only GitHub collector in its own module, with pagination, cache, rate limits and provenance evidence.
- Explicitly distinguish GitHub contributions from public event categories and untracked event classes.
- Consider a self-serve workflow where a user points at their own GitHub username, with no default token and no hidden private data.
- Publish installation and contributor examples only after release acceptance.

## 6. Agent workflow: start here

**First inspection:** read \`AGENTS.md\`, then architecture, contract, design and roadmap. Check \`README.md\` preview images at the actual target display size. Run the 23-test baseline and the export reproducibility check.

**For visual tasks:** submit a concrete before/after screenshot, description of the visual grammar, explanation of source-backed stops and measured readability. Do not just say “more premium” or repaint the same layout.

**For data tasks:** preserve v1 semantics; write tests for unseen IDs, duplicate records, UTC boundaries, invalid Unicode and public/private leakage. Never guess missing GitHub events.

**For infrastructure tasks:** keep local-only development working on Windows, no WSL requirement, no secrets/paid APIs in CI. Respect existing default branch and owner review process.

**For documentation tasks:** correct outdated claims, copy exact behaviour from code, keep user-facing text in British English, explicitly mark synthetic art.

## 7. Definition of accepted work

A change is **not done** merely because a commit exists. Require:
- a tangible improvement matching user feedback;
- tests plus deterministic asset comparison;
- clear data provenance in SVG and README;
- no cross-concept changes;
- no hidden network or private-token dependency;
- accessibility and mobile impact addressed;
- PR evidence including before/after image and limitations;
- owner decision before public release or major design selection.

## 8. Ready-to-use handover prompt

> You are the lead engineer and visual-systems architect for \`AdityaSreevatsaK/Open-Source-Metro\`. First read \`AGENTS.md\` and every linked architecture, data contract, development, design, roadmap and release document. Operate only in this repository. Treat the existing five straight, semantic metro lines over the 53-week contribution calendar as a **candidate baseline**, not a finished design. The owner rejected winding, squiggly routes and requires an immediately understandable, genuinely beautiful GitHub contribution-chart-centred concept. Build code, not just mock-ups. Maintain the synthetic-versus-real provenance boundary, the Python 3.11+ offline workflow, Windows support, tests, and reproducible static SVG previews. Use a feature branch, include screenshots and accessibility/mobile analysis, run verification, and report changed files, exact test results and any blockers. Do not alter GitHub Activity Studio's other concepts, the owner's profile, or repo visibility/releases without approval.

## Addendum | Living Network compact profile prototype

**Current working branch:** `design/living-network-v1`, draft PR #1. This is the preferred visual **candidate**, not a merged release.

The owner approved exploring Living Network because repository routes, chronological replay and source-backed milestone stops communicate more than decorative event-kind lines.

The first full-screen concept is a 1460×938 storyboarding SVG plus interactive HTML. A second profile-sized, 1360×462 edition now exists:

- `src/open_source_metro/compact_profile.py`: independent compact 53-week chart and five aligned source-backed project routes.
- `tools/render_compact_gif.py`: optional 26-frame replay, 850 px wide, station-accurate train arrivals, 2.2-second final hold.
- `assets/living-compact-showcase.svg`, `living-compact-paper.svg`, `living-compact-fixture.svg`: deterministic static previews. Regular CI regenerates and compares them.
- `assets/living-compact-replay.gif`: constrained GIF preview generated from the same source, with optional Pillow/CairoSVG.
- `tests/test_compact_profile.py`, `tests/test_compact_gif.py`: source traceability, UTC positions, provenance, malformed data, final-frame and animation checks.
- `docs/COMPACT_LIVING_NETWORK.md`: reproduction commands, design semantics and acceptance criteria.

The full-size renderer and interactive HTML remain unchanged for comparison. **Never** add synthetic event records when `source="github"`. The compact replay only places a train at the latest observed repository stop; it must not animate a fictional event between stops.

**Remaining gates:** verify real GitHub README appearance, a separately designed mobile-friendly preset, user acceptance, and coverage-aware public GitHub data collection. Do not merge PR #1, tag a release or touch the public profile without explicit approval.
