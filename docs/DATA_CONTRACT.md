# Input data contract (v1)

**Status:** v1 offline snapshot format. This is *not* GitHub's official contribution API response.

## Canonical input

\`\`\`json
{
  "schema_version": "1",
  "source": "demo",
  "generated_at": "2026-11-16T00:00:00Z",
  "user": {
    "login": "sample-dev",
    "url": "https://github.com/example"
  },
  "repositories": [
    {
      "full_name": "sample-dev/aurora",
      "name": "aurora",
      "url": "https://github.com/example",
      "language": "Python",
      "stars": 12
    }
  ],
  "activity": [
    {
      "id": "demo-001",
      "kind": "commit",
      "repo_full_name": "sample-dev/aurora",
      "occurred_at": "2026-08-03T10:20:00Z",
      "url": "https://github.com/example",
      "count": 3
    }
  ]
}
\`\`\`

The complete safe sample is at [examples/demo-activity.json](../examples/demo-activity.json).

## Field rules

| Field | Required | Validation / semantics |
| --- | --- | --- |
| \`schema_version\` | yes | Exact string \`"1"\`. Fail closed for other versions. |
| \`source\` | yes | \`"demo"\` or \`"github"\`; controls explicit provenance wording. |
| \`generated_at\` | yes | ISO 8601, timezone-aware UTC timestamp; governs the displayed cut-off. |
| \`user.login\` | yes | Non-empty printable string, no invalid XML/bidi controls, max 120 chars. |
| \`repositories\` | yes | List, possibly empty; unique \`owner/name\` identifiers. |
| \`repositories[].full_name\` | yes | Unique \`owner/name\`, max 200 chars; untrusted. |
| \`repositories[].name\` | optional | Readable name, default last path component, max 200 chars. |
| \`repositories[].url\` | optional | Safe GitHub HTTPS URL or discarded. |
| \`activity\` | yes | List, possibly empty; each event refers to a listed repository. |
| \`activity[].id\` | yes | Non-empty stable event ID, max 160 chars; conflicting duplicates rejected. |
| \`activity[].kind\` | yes | Exactly one supported type listed below. |
| \`activity[].repo_full_name\` | yes | Exact key from \`repositories[].full_name\`. |
| \`activity[].occurred_at\` | yes | Timezone-aware UTC date-time; order by UTC, then ID. |
| \`activity[].count\` | optional | Integer 1 through 100000; bool and floats rejected; default 1. |
| \`activity[].url\` | optional | Safe GitHub HTTPS URL or discarded. |

Non-authoritative metadata such as language/stars may be included in the input but is not currently used as a visual ranking. Never invent missing attributes.

## Event-kind definitions

- \`commit\` -> **CODE**. Source-reported commit activity units.
- \`pr_opened\` -> **PROPOSE**. Pull request was opened, **not** merged.
- \`pr_merged\` -> **MERGE**. Pull request was merged, distinct from opening.
- \`issue_opened\` -> **DISCUSS**. Issue was opened, **not** all issue/discussion engagement.
- \`release\` -> **SHIP**. Release event.

\`count\` is a *source-provided activity unit count*. Summing unlike events is useful only for illustrative density; it must **not** be relabelled “commits” or “complete contributions”.

## Source coverage and epistemic boundaries

- \`source="demo"\` requires obvious synthetic identification. The density-showcase function may add additional illustration-only events exclusively for demo data; it must never augment \`source="github"\`.
- \`source="github"\` means the input claims publicly observed GitHub events. This does **not** mean all contributions have been retrieved.
- GitHub's public Events API, repository commit history, pull requests and contribution calendar can differ in visibility, counting rules, historical coverage and ownership. No current adapter has proven equivalence.
- Inactive/blank cells mean **absent from the input**, not zero real activity.
- The fixed 53-week period ends at \`generated_at\`; events after that exact instant or outside the displayed period must not be treated as observed.
- Only five repositories are drawn as labelled routes, but the calendar uses every eligible in-window source event from **all supplied repositories**. No arbitrary 240-event cap or partial-day deletion is allowed. Events outside the requested time window and the actual number of observed days/weeks must be disclosed.
- Only real safe public URLs can become clickable in a future interactive preview. The current static exports do not need links.

## Determinism and deduplication

Normalisation collapses identical duplicate IDs and rejects conflicting records sharing an ID. Events are ordered by timestamp and then ID. The normaliser does not call GitHub, generate a new timestamp or mutate the source.

Any future contract change requires a new \`schema_version\`, migration notes, tests, backwards-compatibility discussion and user approval for incompatible changes.

## Privacy and safety

No private repositories, user secrets, access tokens, email addresses from protected sources, hidden organisations, private URLs or connected-account exports in committed sample data without explicit approval. Prefer first-party public self-owned data only when a collector has been separately reviewed.

All strings in JSON are hostile until validated. XML escaping is necessary but insufficient unless invalid Unicode and control characters have also been rejected.

## Future collector hand-off (not yet implemented)

A new source adapter must document: endpoint and GitHub API version, public-only scope, permissions, pagination and truncation, rate limits, timezones, deduplication identity, retry/backoff, ownership mapping, missing categories, cache policy, ETags/conditional requests, and what the resulting visual can and cannot accurately claim. Add these tests before introducing any network data path.


## Optional independent GitHub contribution-calendar layer (`_calendar`)

A real `source="github"` snapshot may include the additional top-level object:

```json
{
  "_calendar": {
    "provider": "github-graphql",
    "kind": "github-profile-visible-contributions",
    "username": "example-user",
    "total_contributions": 123,
    "window_from": "2025-11-18T00:00:00Z",
    "window_to": "2026-11-18T00:00:00Z",
    "days": [
      {"date": "2026-11-17", "count": 3},
      {"date": "2026-11-18", "count": 5}
    ]
  }
}
```

This is **not** an event row and cannot be reverse-engineered into individual commits, project milestones, merges or private-repository metadata. The daily counts are GitHub profile-visible contributions and may include anonymous restricted activity according to account settings. A day not returned by GraphQL is **not observed by this API query**. Never treat absent days as authenticated zeros.

Validation: exact provider/type, matching username, distinct ISO calendar dates, non-negative integer counts, bounded dates and no duplicate entries. Render all supported daily squares from `_calendar` if provided; **do not add public repository `activity` counts** into these GitHub totals. Routes always use only the independent `activity` ledger. Keep both provenance classes in the SVG and export summary. A `source="demo"` fixture is forbidden from carrying an official `_calendar`.
