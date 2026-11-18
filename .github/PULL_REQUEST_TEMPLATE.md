## Why is this change needed?

Describe the user-facing problem and how a first-time viewer benefits.

## What changed?

Describe exact data, code, visual and documentation changes. Include filenames and examples.

## Source / privacy / provenance impact

- [ ] Still no private data or secret tokens
- [ ] Real versus synthetic activity is labelled correctly
- [ ] No events, relationships or counts are invented
- [ ] Omissions, data caps and snapshot coverage remain truthful

## Evidence and verification

- [ ] \`python -m unittest discover -s tests -v\` passed
- [ ] \`python -m open_source_metro --input examples/demo-activity.json --output output\` passed
- [ ] All three committed SVGs match regenerated output byte-for-byte
- [ ] Midnight and parchment previews visually inspected
- [ ] Narrow-width GitHub-readme screenshot inspected (or explicitly blocked)
- [ ] Relevant documentation / \`AGENTS.md\` updated

**Exact test result / CI link:**

**Before / after images (required for visual changes):**

## Risks, breaking changes and rollback

State what could go wrong, what's unverified, and how to revert. Do not claim CI or browser checks you have not run.

## Release impact

Is owner approval required for a visual direction, live account integration, privacy boundary, dependency, release or visibility change?
