# Public Events API collector | Experimental, limited history

\`python -m open_source_metro.public_events USERNAME --output output/public-snapshot.json --compact-svg output/public-compact.svg --mobile-svg output/public-mobile.svg\`

This is the **first live public-data adapter**, not a complete GitHub contributions integration.

## Data guarantees

- Fetches **only** \`GET https://api.github.com/users/{username}/events/public\`. No authenticated user activity, private repository events, token requirements or background polling.
- GitHub documents **a maximum of 300 events from the last 30 days**, plus event delivery delays. The adapter therefore limits itself to three pages of 100 and never claims a full year of coverage.
- Maps **opened PRs**, **merged PRs** (including closed-with-merged), **opened issues** and **published releases** by precise event type/action.
- Current GitHub PushEvent payloads expose \`head\` and \`before\` but do **not** expose a list of commits. To avoid fabricating counts, these pushes are **omitted**. Only older/test payloads with explicit commit SHA lists can become \`kind="commit"\`, with deduplicated SHA counts.
- Records ignored event categories in \`_coverage.skipped_by_reason\`. Always display or retain the disclaimer: **“Public event snapshot, not complete GitHub contributions.”**
- Does not merge unrelated event types into "commits" or infer that another user's repositories belong to the profile owner.
- All source event IDs and timestamps are stable, validated and bounded. Data is deterministic for a fixed API response and collection timestamp.
- Errors such as rate limiting, failed requests or invalid JSON are **failures**, not silently interpreted as zero contributions.
- All output files are local and intended for review before a user chooses to publish them. Generated \`output/\` is gitignored.

## Windows PowerShell

\`\`\`powershell
py -3 -m pip install -e .
py -3 -m open_source_metro.public_events AdityaSreevatsaK --output output/public-snapshot.json --compact-svg output/public-compact.svg
Start-Process .\output\public-compact.svg
\`\`\`

The preview is intentionally sparse: it depicts only supported public events returned by GitHub's recent Events API, not private activity or historical contributions. **It may exclude most commit activity.**

## Why this is only a first step

A faithful GitHub contribution calendar requires a separately designed source collection strategy with coverage accounting across commits, PR reviews, issues and other GitHub contributions, repository ownership/forks, historical timelines and GitHub API pagination. A newer source adapter may add these sources, but it must not promote a shallow public events stream to a complete contributions total.

See [GitHub's Events API](https://docs.github.com/en/rest/activity/events) and [GitHub event payloads](https://docs.github.com/en/rest/using-the-rest-api/github-event-types).

## Privacy and rate limits

- No required secrets, private scopes, or paid API usage.
- Validate user names before building a URL; never accept arbitrary request URLs.
- Do not run collectors in CI. Tests use mocked transport exclusively.
- A current public snapshot is a *user-controlled local file*, not a default repository fixture.
- Respect GitHub rate limits and polling guidance; this CLI makes one bounded request sequence per invocation.
