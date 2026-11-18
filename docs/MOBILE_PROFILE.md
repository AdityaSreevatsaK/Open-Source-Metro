# Dedicated mobile portrait edition

The 53-week compact profile banner is still the primary GitHub README image. The **mobile portrait** is a separate 460 × 808 SVG card designed for narrow screens, with a **truthfully labelled 16-week window**.

Instead of shrinking 371 daily cells into a 360px viewport, mobile shows **16 Sunday-to-Saturday week columns**, seven day rows and up to five recently active repository journeys. Stops remain grounded in the exact underlying v1 events.

## Generate

\`\`\`powershell
py -3 -m open_source_metro.mobile_profile --input examples/demo-activity.json --output output/mobile-fixture.svg
py -3 -m open_source_metro.mobile_profile --input examples/demo-activity.json --output output/mobile-showcase.svg --showcase
py -3 -m open_source_metro.mobile_profile --input examples/demo-activity.json --output output/mobile-paper.svg --showcase --theme paper
\`\`\`

Use \`--showcase\` only with synthetic \`source=demo\`; it rejects \`source=github\`. No CDN, external font, network or token is needed to render.

## Reading the mobile card

- Day squares are **observed event units**, not authoritative GitHub contribution totals.
- Each repository route starts at its first **observed** active week and ends at its last, within this window. Rail lines between stops are schematic, not constant work.
- Large rings are observed merged PRs; diamonds represent observed releases.
- Repository selection prioritises activity **within the last 16 weeks**, unlike the full-year feature set.
- Source omissions and the 16-week window are displayed in the image.
- A real GitHub Events API sample may have only the past 30 days of data despite the 16-week display frame. The image says this explicitly; blanks are not confirmed inactivity.

## Scope and testing

No changes were made to the full Living Network or the compact 53-week export. The portrait view has its own tests for source-backed stops, themes, date bounds, no injected markup, sparse/empty fixtures and deterministic output.

A browser-hosted interactive portrait and true profile-specific personalisation are future work; a static SVG in a GitHub README cannot provide app-like interactions.

## Reviewed demonstration SVG assets

- [Midnight synthetic density showcase](../assets/living-mobile-showcase.svg)
- [Paper synthetic density showcase](../assets/living-mobile-paper.svg)
- [Exact ten-event fixture preview](../assets/living-mobile-fixture.svg)

These three assets are byte-for-byte checked against the renderer's output in GitHub Actions. Real personal snapshots are never embedded in the committed previews.
