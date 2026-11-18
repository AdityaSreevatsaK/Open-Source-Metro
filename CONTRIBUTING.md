# Contributing to Open Source Metro

Thank you for considering a contribution. Open Source Metro is currently **pre-alpha** and the visual direction is still under review.

## Before starting

1. Read [AGENTS.md](AGENTS.md), [Architecture](docs/ARCHITECTURE.md), [Data contract](docs/DATA_CONTRACT.md) and [Design principles](docs/DESIGN_PRINCIPLES.md).
2. For new features or major visual work, open an issue/proposal with a concrete screenshot and source-backed rationale before writing a large patch.
3. Choose a scoped branch from \`master\`, such as \`feat/compact-readme-view\` or \`fix/utc-boundary\`.
4. Do not commit private API responses, secret values, account-specific snapshots, paid-service credentials or unrelated project files.

## Setup and tests

\`\`\`powershell
git clone https://github.com/AdityaSreevatsaK/Open-Source-Metro.git
cd Open-Source-Metro
py -3 -m pip install -e .
py -3 -m unittest discover -s tests -v
py -3 -m open_source_metro --input examples/demo-activity.json --output output
\`\`\`

Use \`python\` instead of \`py -3\` on Linux/macOS. See [Development](docs/DEVELOPMENT.md) for the virtual-environment workflow.

## Code and PR expectations

- Write readable Python 3.11+ and use the standard library where practical.
- Preserve determinism, schema v1 semantics and distinct source-event kinds.
- Source snapshots are untrusted. Keep data validation and XML escaping intact.
- Never add invented events to a real source snapshot.
- Do not alter the straight five-service semantics without showing and discussing the rendered replacement.
- Include regression tests for behaviour changes and regenerate the three SVG assets if render output changes.
- Add before/after images for visual modifications, including sparse and dense data examples.
- Document user-visible changes, limitations and unverified claims.
- Keep PRs small and focused; do not merge your own work without project-owner approval.

## Reporting defects

Include the Python version, OS, minimal **synthetic** v1 JSON, command, expected output, actual output and a safe SVG screenshot. Redact any tokens/private URL data.

For security concerns, follow [SECURITY.md](SECURITY.md) instead of publishing exploit details in a public issue.

## Release and licence

Contributions are provided under the repository's MIT licence. No stable release has been approved; see [Release checklist](docs/RELEASE_CHECKLIST.md). The maintainers may reject technically valid changes that reduce interpretability or obscure data provenance.
