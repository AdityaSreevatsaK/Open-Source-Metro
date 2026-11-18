# Migration record: GitHub Activity Studio to Open Source Metro

## Source

Old experimentation home:
- Repository: \`AdityaSreevatsaK/GitHub-Activity-Studio\`
- Working branch: \`concept/open-source-metro\`
- Working directory: \`concepts/open-source-metro/\`
- Shared sample: \`shared/fixtures/demo-activity.json\`
- Historical draft PR: https://github.com/AdityaSreevatsaK/GitHub-Activity-Studio/pull/4

New standalone home:
- Repository: \`AdityaSreevatsaK/Open-Source-Metro\`
- Branch: \`master\`
- Package: \`src/open_source_metro/\`

## Included files and rationale

| Old path | New path | Reason |
| --- | --- | --- |
| \`metro_atlas.py\` | \`src/open_source_metro/renderer.py\` | Most recent user-directed straight-line renderer |
| \`calendar_metro.py\` \`normalise()\` subset | \`src/open_source_metro/validation.py\` | Canonical v1 validation without old visual renderer |
| \`tests/test_metro_atlas.py\` | \`tests/test_renderer.py\` | Existing Atlas regression coverage |
| \`shared/fixtures/demo-activity.json\` | \`examples/demo-activity.json\` | Known, labelled synthetic 10-event sample |
| \`exports/atlas-{...}.svg\` (3) | \`assets/\` | Reproducible, README-ready previews |

The renderer's local import of \`calendar_metro.normalise\` was replaced with \`open_source_metro.validation.normalise\`. Test fixture paths and CLI defaults were rewritten to the new project structure. The implementation was validated with **23 local tests** and byte-for-byte matching of three SVGs.

## Deliberately not migrated

- Legacy independent metro-map renderer and tests (\`metro.py\`).
- Previous calendar-metro generator and old SVG/HTML exports, apart from its reusable normalisation logic.
- GitHub Activity Studio's root README, multi-concept agent briefs, and any data from Agent Swarm, Developer World, Code Factory or Constellation.
- GitHub account-specific contribution snapshots, tokens or private data.
- Historical branches, PR metadata and repository administration settings.

The old repo and its PR remain untouched. Changes to them require explicit authorisation.

## Consequences

- This is a **clean extraction**, not a full Git history transfer. The historical commits remain visible in the source repository.
- This project's own versioning and CI now start independently.
- SVGs in \`assets/\` are static and include explicit synthetic provenance.
- Legacy preview links from the old repo do not become authoritative documentation here.
- The new repo was already **public** when migration began. No new private or account-specific data was added.
- Repository About description/topics may require GitHub administration UI because the available connector's GitHub actions do not expose repository-metadata editing.
