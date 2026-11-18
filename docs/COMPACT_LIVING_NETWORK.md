# Compact Living Network and replay | Design candidate

This is an additive, **profile-width edition** of the repository-specific Living Network design, not a replacement for the full storytelling canvas. The full SVG and interactive HTML from the original draft remain available.

## Why it exists

The 1460×938 storyboard works for a detail view but becomes too small to read in a GitHub profile README. The compact version is 1360×462, with the calendar above five aligned repository timelines. The visual still represents a 53-week Sunday-first grid, source event-kind milestones and at most five source-backed repositories.

## What the animation means

- Each project is a coloured repository journey, beginning at its first **observed activity week** and ending at its last.
- Circular stop: a source-observed week. Small ring: recorded PR merge. Diamond: recorded release.
- The replay reveal advances chronologically; a tiny train stays at each repository's **latest observed stop** as of that frame. It does **not** interpolate a fictional event at an unobserved week.
- A moving timeline cursor indicates progress; the final frame hides it, reveals the whole network and holds for 2.2 seconds.
- A blank calendar day means **not observed in the input**, not an official GitHub count of zero.
- The synthetic showcase adds exactly 108 illustrated events and is prominently marked fictional. Real public snapshots cannot be expanded with this generator.

## Export on Windows

Requires Python 3.11+ and a local checkout:

\`\`\`powershell
py -3 -m pip install -e .
py -3 -m open_source_metro.compact_profile --input examples/demo-activity.json --output output/compact-showcase.svg --showcase
py -3 -m open_source_metro.compact_profile --input examples/demo-activity.json --output output/compact-paper.svg --showcase --theme paper
py -3 -m open_source_metro.compact_profile --input examples/demo-activity.json --output output/compact-fixture.svg

# Optional GIF: core renderer has no CairoSVG/Pillow requirement
py -3 -m pip install -e ".[animation]"
py -3 tools/render_compact_gif.py --input examples/demo-activity.json --output output/compact-replay.gif --showcase --frames 26 --width 850
\`\`\`

The GIF is deliberately restrained, with observed-stop arrivals and a hold on the completed network. It is a README visual, while the original full browser preview remains the place to inspect individual source events.

## Acceptance conditions

- Keep the full Living Network renderer unchanged until a design is chosen.
- Validate source-event provenance, UTC alignment, marker semantics and accessible SVG title/desc.
- Test the compact output at an approximately 850px GitHub desktop width and 320–420px mobile viewport. The mobile version may still need a dedicated separate preset.
- Preserve static GIF fallback and provide a clearly labelled synthetic demo.
- Do not interpret route links as actual GitHub collaborations or project dependencies.
- Do not merge the draft PR, update a live GitHub profile or publish a stable release without owner approval.

## Review and CI status

Three static compact exports are generated deterministically from the committed ten-event fixture and compared byte-for-byte on Windows/Linux CI. The compact GIF is generated with optional CairoSVG/Pillow tooling, but its pixel bytes are not required to match across runners because rasterisation and installed fonts may vary. CI checks its GIF signature, 850 px width and size bound.

Current compact outputs: `assets/living-compact-showcase.svg`, `assets/living-compact-paper.svg`, `assets/living-compact-fixture.svg`, and `assets/living-compact-replay.gif`.

The original full-size Living Network renderer, HTML replay, GIF and the primary `open-source-metro` entry point have not been replaced. The compact source and gallery remain inside the design draft PR until approval.
