# Development guide

## Supported baseline

- Python **3.11+**.
- Windows 10/11 PowerShell and PyCharm supported without WSL; Linux/macOS work with \`python\` instead of \`py -3\`.
- Runtime: Python standard library, deterministic SVG output.
- Installation/build: setuptools through \`pyproject.toml\`.
- GitHub Actions: Ubuntu and Windows on Python 3.11/3.12, no secrets, no paid API calls.

## First checkout on Windows

\`\`\`powershell
git clone https://github.com/AdityaSreevatsaK/Open-Source-Metro.git
cd Open-Source-Metro

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s tests -v
python -m open_source_metro --input examples/demo-activity.json --output output
Start-Process output\atlas-midnight-showcase.svg
\`\`\`

If PowerShell blocks local activation, run \`.\.venv\Scripts\python.exe\` directly rather than changing system execution policy.

### Linux / macOS

\`\`\`bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m open_source_metro --input examples/demo-activity.json --output output
\`\`\`

## PyCharm

1. Open repository root.
2. Configure a Python 3.11+ interpreter under project settings, preferably \`.venv\`.
3. Install project in editable mode using terminal \`python -m pip install -e .\`.
4. Mark \`src\` as Sources Root only if required by the IDE; it should work without this after installation.
5. Run \`tests/\` as a Python \`unittest\` directory and \`open_source_metro\` as a module.
6. Keep generated \`output/\` untracked.

## CLI and programmatic API

\`\`\`powershell
python -m open_source_metro --input examples/demo-activity.json --output output
open-source-metro --input examples/demo-activity.json --output output
\`\`\`

The command writes:
- \`atlas-midnight-fixture.svg\`: exactly the original sample events.
- \`atlas-midnight-showcase.svg\`: fixture plus explicitly artificial, deterministic illustration activity.
- \`atlas-parchment-showcase.svg\`: same illustration activity with a second theme.

**Caution:** \`generate()\` currently includes showcase outputs even when given a custom source. For \`source="github"\`, showcase expansion deliberately raises \`ValueError\`; render a single real snapshot directly using \`render(data, theme)\` until a dedicated real-snapshot CLI export mode is implemented. Never bypass this restriction.

Programmatic use:

\`\`\`python
import json
from pathlib import Path
from open_source_metro import render, normalise

raw = json.loads(Path("examples/demo-activity.json").read_text(encoding="utf-8"))
validated = normalise(raw)
svg = render(raw, theme="midnight")
Path("output/example.svg").parent.mkdir(exist_ok=True)
Path("output/example.svg").write_text(svg, encoding="utf-8")
\`\`\`

\`normalise\` takes raw JSON dictionaries. \`render\` likewise accepts raw v1 JSON and validates internally. Do not feed a pre-normalised dictionary into \`render\` unless you add explicit support.

## Testing and reproducibility

Full unit suite:

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

Check the three generated assets against committed previews:

\`\`\`powershell
python -m open_source_metro --input examples/demo-activity.json --output output
@('atlas-midnight-fixture.svg','atlas-midnight-showcase.svg','atlas-parchment-showcase.svg') | ForEach-Object {
  $name = $_
  if ((Get-FileHash "assets\$name" -Algorithm SHA256).Hash -ne (Get-FileHash "output\$name" -Algorithm SHA256).Hash) {
    throw "Preview mismatch: $name"
  }
}
\`\`\`

The GitHub Actions matrix performs the same byte comparison and unit tests. **Do not claim CI passed until the latest workflow status is actually verified.**

### Expected regression classes

- Date semantics: UTC, Sunday/Saturday positions, 53-week grid, snapshot cut-off.
- Malformed data: schema, unknown kind, missing repo, invalid counts, conflicting IDs, unsafe text/URLs.
- Empty and one-station charts.
- Five straight service lanes with source-backed week markers.
- Repository terminal provenance, event omissions and 240-event day boundaries.
- Demo-only synthetic expansion, stable seeds and original fixture fidelity.
- Exact SVG reproducibility, accessible \`title\` and \`desc\`, light/dark output.

## Changing visuals safely

1. Capture a before-render image, not just SVG text.
2. Explain what users should understand faster after the change.
3. Preserve calendar grammar and straight five-lane tracks unless the owner approves a new direction.
4. Add tests for route semantics and XML validity.
5. Regenerate \`assets/*.svg\` from the committed fixture.
6. Compare full-width and narrow-width previews, midnight and parchment.
7. Update README alt text and design notes.
8. Include screenshot/previews and trade-offs in the PR.

Avoid mechanical code cleanup that changes visual output without a deliberate design goal.

## Dependencies and tooling

No Node.js, Docker, WSL, browser automation, secrets or external API are required for baseline development. Adding them to the core path requires a concrete, measured benefit and clear installation steps. Do not add GitHub tokens to examples or workflows.

## Common problems

- \`ModuleNotFoundError: open_source_metro\`: run \`python -m pip install -e .\` in your active interpreter.
- Blank/empty calendar: inspect \`generated_at\` and whether activity lies within the 53-week window. Empty does not prove zero GitHub contributions.
- Incomplete repo coverage: only five featured repositories are currently shown; this is disclosed visually.
- Static SVG does not animate in GitHub: that is expected. Do not depend on inline SVG animation in README.
- Comparison fails after a design change: regenerate, inspect and commit all three changed previews with tests.
