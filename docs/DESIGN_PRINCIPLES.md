# Design principles | Calendar × Metro

## Product north star

Someone arriving on a GitHub profile should immediately recognise a **contribution calendar**, understand that coloured features represent **different event types**, and find the featured repositories without deciphering a complex map.

We are not reproducing Platane/snk, a generic GitHub statistics card, a literal transit map on a separate canvas, or a heatmap covered in decorative squiggles.

Aesthetic standard: **premium, memorable, readable, information-led**. Engineering correctness does not automatically make artwork attractive.

## What users rejected and what we kept

Early iterations rendered disconnected, confusing, squiggly routes and felt lacklustre. The current baseline uses five **parallel, horizontal transport lines** aligned with grid row gutters. This is easier to parse but remains a **candidate**. Future agents should improve typographic rhythm, station identity, line hierarchy and mobile scaling rather than merely adjusting colour hex codes.

Do not conflate a route with an actual journey to another repository. The track is a code for *event type*, not a fictional causal relationship.

## Visual hierarchy

1. **Title and provenance:** Open Source Metro with immediately visible “SYNTHETIC DENSITY SHOWCASE”, “SHARED SYNTHETIC FIXTURE”, or “PUBLIC EVENT SNAPSHOT”.
2. **Calendar:** 53 Sunday-to-Saturday weeks, seven days, truthful date positions, recognisable square tiles.
3. **Service lanes:** five clear and separately identifiable rail tracks (CODE, PROPOSE, MERGE, DISCUSS, SHIP).
4. **Stops:** exact weeks with source-backed events of that kind. No stops for dates without an input event.
5. **Terminals / directory:** prominent numbered stops tie back to real selected repositories from the input.
6. **Legend and caveats:** green intensity, omitted data, source limits, and the difference between event units and total contributions.

## Graphic rules

- Keep service lanes perfectly straight unless a new design has been separately approved.
- Distinguish all five services with colour **and text**, not colour alone.
- No invented transitions, fake “trains” between unrelated repositories, overlaid arrows on every cell, random ornaments or unreadable crossings.
- Use fixed layout geometry, stable typography and predictable visual weight.
- Labels must not collide with tiles, stops or each other; add measured spacing.
- Ensure a full contribution year is readable even when only ten source events exist.
- Do not let a dense showcase disguise the scarcity of the actual fixture.
- Terminal numbers must map one-to-one to a disclosed repository directory.
- Keep tracks and station markers clear at README embed sizes; include a compact alternative if needed.
- Preserve neutral blank-day styling. Never paint blanks as verified inactivity.

## Theme directions

**Midnight:** restrained navy surfaces, crisp luminous service colours, high-contrast white typography, clear light-green calendar intensity.

**Parchment:** warm paper surfaces, disciplined vintage typography and slightly muted service colours. It must remain legible rather than distressed or ornamental.

Accessibility minimum: descriptive SVG \`title\` and \`desc\`, meaningful alt text in README, text contrast targeted to WCAG AA, reduced motion when animation is added, and meaningful interpretation without hover or JavaScript.

## Mobile, GIF and GitHub constraints

The output is static, not an interactive page inside GitHub. GitHub may rasterise/proxy SVG and does not guarantee embedded SMIL animation. Aim for a fully meaningful still image. Test ~320–420px viewport screenshots, desktop README widths, light and dark GitHub UI. A browser companion may offer zoom, filter, hover, focus and event lists, but must not replace the accessible static export.

## Provenance-first visual semantics

- Days coloured by observed event units, not official complete contribution counts.
- Week stops by observed kind, not inferred engagement or activity between recorded weeks.
- Repo terminals by a selected recorded event, not invented “projects completed”.
- Omitted events/repositories disclosed in output.
- Showcase illustrations separated from raw synthetic fixture and real public data.

## Design review scorecard

| Quality | Acceptance question |
| --- | --- |
| Immediate clarity | Can a first-time viewer explain the grid and five lines in under 10 seconds? |
| Visual distinction | Does it look recognisably like Open Source Metro, not a standard chart skin? |
| Information integrity | Can every marked date, stop and repository be traced to an input event? |
| Contrast | Do labels remain readable over both themes? |
| Mobile | Is the profile embed meaningful without pinch zoom? |
| Visual balance | Does a sparse real input still look intentional rather than broken? |
| Density | Does a busy year avoid occlusion and illegible labels? |
| Accessibility | Are colour-independent labels and accessible source explanations present? |
| Performance | Does export run offline, quickly, deterministically, without paid services? |

Prefer a side-by-side image comparison and test evidence to long verbal arguments about design. Seek owner feedback on the actual visual before declaring a redesign complete.
