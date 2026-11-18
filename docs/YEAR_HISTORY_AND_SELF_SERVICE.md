# Year-scale public repository history | Collection contract

**Status:** Public-repository source collector, not an official GitHub contributions API, and not a production-ready all-account timeline.

## Why this collector exists

The original \`public_events.py\` samples at most 300 public Events API records from the last 30 days. It cannot describe a 53-week development history. \`year_history.py\` separately queries **public repository histories**, up to a requested 30-370-day window. It can reveal *some* source-backed, older milestones, and maintains a detailed, explicit coverage manifest.

The primary GitHub Live Network is still a faithful **event visualisation** of the **supplied** snapshot, not a faithful clone of GitHub's profile contribution totals.

## Example, Windows PowerShell

First install once:

\`\`\`powershell
git clone https://github.com/AdityaSreevatsaK/Open-Source-Metro.git
cd Open-Source-Metro
py -3 -m pip install -e .
\`\`\`

Collect public repository history for the default ten **time-diverse, non-fork owned public** repositories (recent plus progressively older projects):

\`\`\`powershell
py -3 -m open_source_metro.year_history AdityaSreevatsaK --days 365 --max-repos 10 --pages 2 --output output/year-public.json
\`\`\`

Collect from **explicit public repositories**, including repositories belonging to other owners where the specified user has authored activity:

\`\`\`powershell
py -3 -m open_source_metro.year_history AdityaSreevatsaK --repos "AdityaSreevatsaK/Open-Source-Metro,AdityaSreevatsaK/GitHub-Activity-Studio" --output output/year-selected.json
\`\`\`

Open \`output/year-public.json\`, especially \`_coverage\`, before claiming any contribution totals. The collector does not access private repositories by default or save a GitHub access token.

### Complete self-service profile export

Single command using real public history:

\`\`\`powershell
py -3 -m open_source_metro.profile_cli --username AdityaSreevatsaK --output output/my-profile --layout both --theme midnight
\`\`\`

Or reproducible **offline mode**, with no network activity:

\`\`\`powershell
py -3 -m open_source_metro.profile_cli --input examples/demo-activity.json --output output/demo-profile --layout both
\`\`\`

Narrow the profile to specific already-collected repository names:

\`\`\`powershell
py -3 -m open_source_metro.profile_cli --input output/year-public.json --featured "AdityaSreevatsaK/Open-Source-Metro" --output output/metro-only --layout both
\`\`\`

Specify the collection scope separately using \`--repos\` **only with \`--username\`**. \`--featured\` filters *already collected* repositories, it cannot add missing historical data. The generated pack includes:

| File | Purpose |
| --- | --- |
| \`source-snapshot.json\` | Exact validated source data, source coverage and manual selection metadata |
| \`profile-compact.svg\` | Full 53-week GitHub README profile format |
| \`profile-mobile.svg\` | Explicitly recent 16-week narrow portrait |
| \`README_SNIPPET.md\` | Manual embed guidance with provenance warnings |

**Nothing is automatically committed to the owner's actual GitHub profile.** No SVG generated from the real username is bundled in this project's examples.

## Precisely what is collected

| Endpoint | Observed event | Important limitation |
| --- | --- | --- |
| \`GET /users/{username}/repos\` | Public repository discovery, owner only by default | Organisations, contributed-to repos and forks excluded unless explicitly included |
| \`GET /repos/{owner}/{repo}/commits?author=...\` | Individual linked commits with their real SHA and author UTC date | **Current default branch only**, not all branches or all GitHub profile contributions |
| \`GET /repos/{owner}/{repo}/pulls?state=all\` | PR opened and PR merged for PRs authored by the selected user | Pagination and opened-date ordering can omit PRs created long ago and merged recently |
| \`GET /repos/{owner}/{repo}/issues?state=all&creator=...\` | Issues opened by the user; PR objects discarded | No issue comments, reviews or discussions |
| \`GET /repos/{owner}/{repo}/releases\` | Releases published by the selected user | No releases published by someone else |

The presence of a pull request on a public repository does **not** make it the user's PR. Identity is checked against the source author. We count a PR merge milestone only when the PR itself was authored by the selected user.

Every captured commit becomes a single source event with \`count=1\`, not an extrapolated count. A PR merged by another maintainer can still appear as a merged PR authored by the selected user.

## Coverage and omissions

The \`_coverage\` field includes:

- Exact requested window and collection timestamp.
- Whether repository selection was automatic or explicitly supplied.
- Repository list and per-repository endpoint fetch counts.
- Per-endpoint pagination-cap flags.
- Repository discovery cap indication.
- A \`possible_history_truncation\` flag.
- Known blind spots.

**Even when \`possible_history_truncation\` is false, the snapshot is not complete GitHub contributions.** A complete API page cannot prove no omitted events elsewhere, and this collector deliberately excludes many kinds of contribution.

Default request bounds: 10 repositories; up to 2 pages of 100 entries per endpoint and discovery. All bounds are configurable within 1-20 repositories and 1-5 pages, with a maximum 370-day window. More repositories/pages may hit unauthenticated rate limits.

No network queries run in CI; the public collector is tested using injected mock HTTP responses.

## Optional GitHub token

To avoid GitHub's low unauthenticated limit, use a token as an **optional environment variable**, preferably a fine-grained, read-only token:

\`\`\`powershell
$env:GITHUB_TOKEN = "<TOKEN_SET_LOCALLY>"
py -3 -m open_source_metro.profile_cli --username AdityaSreevatsaK --output output/my-profile
Remove-Item Env:GITHUB_TOKEN
\`\`\`

Never paste actual token values into committed docs, GitHub issues, PR comments or SVG files. The token is only sent in an Authorization header to \`api.github.com\`; it is never written to \`source-snapshot.json\`.

The repository remains public, and the collector may only include source rows whose API metadata explicitly confirms \`private: false\`.

## Source and endpoint references

- [GitHub REST: list repositories for a user](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
- [GitHub REST: list commits](https://docs.github.com/en/rest/commits/commits#list-commits)
- [GitHub REST: pull requests](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests)
- [GitHub REST: issues](https://docs.github.com/en/rest/issues/issues#list-repository-issues)
- [GitHub REST: releases](https://docs.github.com/en/rest/releases/releases#list-releases)
- [GitHub REST: pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api)

### Future extension, not yet implemented

A more complete collector would need additional coverage of public organisation repositories, forks, default-branch changes, authored PRs across external repositories, and authenticated GraphQL contributions collection. Each source must be independently verified with limits, costs, rate handling and privacy controls before it becomes part of the published source contract.


## No-code workflow: GitHub Actions (manual, opt-in)

A one-off self-service workflow is installed at [Generate public Metro profile](../.github/workflows/generate-public-profile.yml). After this feature merges into the default branch:

1. Open the repository's **Actions** tab.
2. Select **Generate public Metro profile (manual)**.
3. Choose **Run workflow** and supply a public GitHub username; optionally choose public repository scope, featured repositories, theme and layout.
4. Open the completed run and download the **open-source-metro-public-profile** artifact, which includes SVGs, source JSON and the README snippet.
5. Review the **_coverage** manifest and only then decide whether to manually embed the SVG in a GitHub profile.

The workflow uses a short-lived read-only GitHub Actions token to increase public API allowance, performs no Git push, has no account-write permissions and retains downloadable artifacts for **seven days**. Actions artifacts from a public project may be visible to others: use only information you are comfortable sharing publicly. The workflow is **not scheduled** and does not automatically update any profile.

The automated unit test workflow makes **zero real network requests**, uses synthetic and mocked data, and cannot prove that an arbitrary GitHub account's entire development history is captured.


## Why the old profile image looked nearly empty

The initial export used only five most recently pushed repositories and an unnecessary 240-event renderer cap. On a real run, 502 events were fetched but the chart kept only 207 and reported **295 omitted**. The selected projects were so recent that the visible map had about a week of activity. This was a poor representation of a year, not evidence that the GitHub account was inactive.

Corrections:

1. The **annual calendar now uses all source events in its 53-week window**, from every repository present in the snapshot. Up to five observed-active repositories become labelled routes; other repositories still influence the day squares.
2. Automatic public repository selection now spans **ten** repositories by default, combining recent and progressively older projects from the public, pushed-date-sorted list. This remains a bounded sample rather than account-wide collection.
3. The SVG displays **actual observed date range**, **weeks with observations**, and explicitly distinguishes unfeatured routes from events outside the year.
4. The generated README snippet includes a data-coverage summary and highlights sparse history.
5. To explore other public repos, specify a reviewed comma-separated `--repos` list. This changes the collection scope, not the rendered numbers' honesty.

Do not infer that a blank annual chart signifies no GitHub contributions. It means this selected public source had no observations for those dates. It can still omit external PRs, private activity, branch contributions and other GitHub event types.

### Project-route ranking for real source snapshots

The five labelled project routes prefer repositories with activity across **more distinct observed weeks**, rather than favouring one extremely busy day. Event volume then breaks ties. This avoids five newly created repositories crowding older, sustained public work out of the map. The annual calendar still includes every observed event from the collected public repositories, even those that are not given individual routes. For a different set of routes, choose a reviewed `--featured` list.
