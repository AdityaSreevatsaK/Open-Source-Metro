# AGENTS.md | Open Source Metro

> **Canonical operating instructions for human contributors and AI coding agents.**
> Read this file **first**, then the referenced documents. Treat it as an engineering contract, not as marketing copy.

## 1. Mission and product boundaries

Open Source Metro is a **standalone**, reusable, Python-based visualisation engine that presents **source-backed GitHub event activity** through a recognisable contribution-calendar grid and a coherent transport-map metaphor.

We are building a visually excellent and understandable **open-source product**, not a toy animation or generic contribution badge. The output should make sense to a first-time GitHub visitor without a lengthy explanation.

The *calendar is the foundation*. It has 53 Sunday-to-Saturday weekly columns and seven weekday rows. The *metro* is a second, clearly legible layer. Five distinct types of source events use five **straight, parallel** tracks. Dated roundels denote recorded active weeks; numbered repository terminals identify individual repositories. Never confuse a schematic track with evidence of activity between stations.

**User feedback is binding:** previous freehand, criss-crossing / squiggly transit paths were rejected as confusing. Never reintroduce wandering curves, arbitrarily connected events, or crossing routes merely to make the image look busy. Prioritise beauty **and** semantic clarity.

## 2. Repository scope and governance

- Canonical repository: https://github.com/AdityaSreevatsaK/Open-Source-Metro
- Original exploratory source (reference only): https://github.com/AdityaSreevatsaK/GitHub-Activity-Studio/tree/concept/open-source-metro
- The standalone repository is **not** part of any other GitHub Activity Studio concept.
- Work only inside this repository. Never modify GitHub Activity Studio's other concept branches, the owner's live profile repository, GitHub account metadata or external project repositories.
- Do not publish a release, enable external services, change repository visibility, modify repository administration settings or merge substantial redesigns without explicit owner approval.
- The repository was created as **public**. Assume every committed item can be viewed immediately. Use synthetic, publicly safe data only.
- The default branch is \`master\`. Prefer a purpose-specific feature branch and an evidence-rich PR for substantial work. Direct default-branch changes require owner instruction.
- **No real-account snapshots are committed without explicit approval and a provenance/privacy review.**
- Do not make unsupported claims about what GitHub has verified or about complete contribution history.

## 3. Read in this order

1. [README.md](README.md): identity, current previews, installation and limitations.
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): modules, transformation pipeline, extension points.
3. [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md): strict v1 input semantics, security and provenance.
4. [docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md): visual identity, layout and forbidden design shortcuts.
5. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): Windows-first execution, testing and export reproducibility.
6. [docs/ROADMAP.md](docs/ROADMAP.md): prioritised product backlog and decision gates.
7. [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md): minimum evidence needed before a public release.
8. [docs/AGENT_HANDOVER.md](docs/AGENT_HANDOVER.md): decisions, current status and next work.
9. [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## 4. Repository layout and ownership

| Path | Responsibility | Key rule |
| --- | --- | --- |
| \`src/open_source_metro/validation.py\` | Input validation, UTC dates, URL hygiene, deterministic source-event normalisation | Never weaken validation to accommodate invalid fixtures |
| \`src/open_source_metro/renderer.py\` | Calendar positioning, five metro tracks, stations, accessible SVGs, CLI | Keep tracks straight and event-based; no hidden network access |
| \`src/open_source_metro/__main__.py\` | \`python -m open_source_metro\` entry point | Stable CLI contract |
| \`examples/demo-activity.json\` | Only shared synthetic v1 sample data | Treat all demo IDs/names as invented |
| \`assets/*.svg\` | Three committed static README-ready examples | Must be byte-for-byte regenerable |
| \`tests/\` | Offline safety, semantic, determinism and export regression tests | Add regression tests for behavioural changes |
| \`.github/workflows/ci.yml\` | No-token Linux/Windows validation | No paid APIs, credentials or private downloads in CI |
| \`docs/\` | Specification, architecture, design, handovers and release gates | Keep docs in sync with code |
| \`pyproject.toml\` | Installable Python project | Standard-library runtime, Python 3.11+ |

Do not migrate the old \`calendar_metro.py\`, \`metro.py\`, old browser prototype, old generator test suite or unrelated concepts without a specific approved reason. The new renderer's only historical dependency was the v1 normaliser, which is now extracted into \`validation.py\`.

## 5. Absolute accuracy and data requirements

- Only \`schema_version: "1"\`, \`source: "demo"|"github"\` and valid UTC timestamps are accepted.
- Event types are exactly \`commit\`, \`pr_opened\`, \`pr_merged\`, \`issue_opened\`, \`release\`. Never collapse them into “commits”.
- Event \`count\` means supplied source-backed units, not necessarily the GitHub contribution total.
- No fabricated real activity, achievements, relationships, repository ownership or dates.
- Blank day means **no observation in the supplied snapshot**, **not** proven zero contributions.
- Synthetic density showcases are allowed **only** with \`source="demo"\` and must retain prominent “synthetic” wording.
- The fixture-only illustration must remain an exact, non-augmented rendering of the supplied sample.
- Source input is untrusted. Escape displayed text, validate and strictly bound IDs, repository metadata and counts; reject conflicting duplicate IDs and invalid Unicode.
- No private data, secrets, tokens or authorisation headers in SVGs, logs, tests, docs or CI outputs.
- If coverage is incomplete, state that explicitly both in output and documentation. A future GitHub collector is a separate, reviewed workstream, not a shortcut.

## 6. Visual and accessibility requirements

**Must preserve:** a clearly recognisable 53 × 7 contribution grid; correct months and weekday alignment; five unambiguous, straight service lanes; route-to-event-kind correspondence; roundel-to-week correspondence; source-backed terminal dates; labelled legend; explicit “demo” or “public snapshot” provenance; omission disclosure.

**Must not do:** squiggly/freehand routes, arbitrary curves between unrelated repositories, unreadable intersection spaghetti, fake source URLs, animations that are essential for interpreting the graphic, or replacing the grid with a wholly separate metro map.

Treat the current Metro Atlas as a **design candidate**, not a design approval. The user described earlier iterations as confusing and lacklustre. Improve composition, typography, station meaning, rhythm and mobile readability. Avoid superficial colour-only changes.

Static SVG is the canonical GitHub README asset. A future interactive browser layer must be additive, keyboard usable, readable with assistive technology and respect reduced-motion. Provide a faithful light and dark direction with reasonable contrast. Avoid real transit company branding.

## 7. Agent operating procedure

Before code:
1. Read required files and inspect relevant tests.
2. Articulate the precise problem, affected files and expected user-visible effect.
3. Check whether a request belongs to the renderer, source contract, UI, docs, CI or future collector.
4. Identify how the change will affect the demo/real-data boundary and generated SVG reproducibility.

During code:
1. Make small, reviewable commits. Avoid broad mechanical rewrites and avoid breaking CLI import paths.
2. Keep render functions deterministic: no implicit current date, random unseeded state, external fonts or network calls.
3. Prefer standard-library solutions. Additional runtime dependencies need a documented reason.
4. Use British English in documentation and visible strings.
5. Keep fixtures and security cases local and synthetic.
6. Cover normal, empty, one-repository, dense, malicious and boundary inputs where relevant.

Before declaring done:
1. Run \`python -m pip install -e .\` in a clean environment.
2. Run \`python -m unittest discover -s tests -v\`.
3. Run \`python -m open_source_metro --input examples/demo-activity.json --output output\`.
4. Compare all three \`output/*.svg\` files byte-for-byte with the corresponding checked-in \`assets/*.svg\`.
5. Review dark and parchment SVG outputs as actual images, including at roughly 320–420 px viewport width.
6. Verify CI statuses, if available. Never label unrun or unavailable checks as passing.
7. Update docs, known limitations and the release checklist.
8. Provide the user with changed files, precise validation results, caveats and branch/PR links.

## 8. Definition of done for a change

- User-visible goal met, not just described.
- Accurate v1 data/provenance semantics retained.
- Tests added or reasonably updated; local suite and deterministic preview comparisons pass.
- No external network or private-data requirement introduced.
- README and agent documentation remain accurate.
- No unrelated files, branches or repositories touched.
- Accessibility and responsive behaviour considered.
- Unverified claims/metrics are explicitly labelled as unverified.

## 9. Recommended specialisations for parallel AI agents

- **Visual systems agent:** composition, transit grammar, static previews, mobile legibility, visual regression evidence.
- **Data and provenance agent:** contract, validation, event semantics, omissions and future collector design.
- **QA/security agent:** tests, input safety, SVG/XML injection, reproducibility, CI, accessibility.
- **Documentation/product agent:** README, examples, contributor journeys, design rationale, release readiness.

Agents must not race on the same files or independently build conflicting collectors. Coordinate through a PR and this document.

## 10. Product truths that must survive future refactors

The project is **not** an official GitHub chart replacement, complete GitHub contributions API, live collector, real-user metrics report or released production tool. It is an open-source-bound, tested, **offline** graphic prototype with truthful fixture data and clearly labelled illustration-only variants.

**Optimise for intelligibility before spectacle.**
