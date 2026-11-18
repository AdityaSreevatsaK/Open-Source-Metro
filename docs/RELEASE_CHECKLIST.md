# Public release readiness checklist

**Do not tag v1.0, publish to PyPI or alter a live GitHub profile until the owner explicitly approves.** The repository is public but the product is pre-alpha.

## Design sign-off

- [ ] Design chosen after side-by-side owner review.
- [ ] Viewer can recognise a GitHub-style calendar and explain the metro lines at a glance.
- [ ] All five event kinds and active-week stops are accurate.
- [ ] No arbitrary squiggles, invented relationships or misleading traffic.
- [ ] Sparse and dense inputs both look intentional.
- [ ] Meaningful at desktop and narrow/mobile GitHub README widths.
- [ ] Midnight and parchment styles have acceptable contrast; legends work without colour.
- [ ] SVG \`title\`, \`desc\`, README alt text and any browser keyboard flow are validated.

## Functional validation

- [ ] Python 3.11+ clean installation on Windows PowerShell without WSL.
- [ ] Python 3.11+ clean installation on Linux.
- [ ] Entire \`unittest\` suite passes locally.
- [ ] Latest GitHub Actions Windows + Linux matrix passes, not just configured.
- [ ] All three checked-in SVG examples exactly reproduce.
- [ ] Empty, one-repo, multiple-repo, missing data, malformed input, high-density and cap-boundary behaviour tested.
- [ ] UTC and Sunday-to-Saturday alignment tested at calendar-year boundaries.
- [ ] All user-controlled SVG text and URLs validated/escaped.
- [ ] Output SVG file sizes are suitable for GitHub.
- [ ] Official GitHub README image proxy tested with both themes.

## Data semantics and privacy

- [ ] Demo artwork prominently labelled and completely synthetic.
- [ ] Fixture-only render not augmented.
- [ ] Public snapshot never filled with synthetic contributions.
- [ ] “Blank means not observed” is stated.
- [ ] Event kinds and counts are not falsely described as complete contribution totals.
- [ ] Source coverage, omitted events, repository limits and rate-limiting documented.
- [ ] No secrets, private user activity, owner contact data or unapproved API tokens in any commit or generated artefact.
- [ ] Public-data collector, if added, separately threat-modelled and reviewed.

## Open-source engineering

- [ ] README matches current executable CLI and screenshots.
- [ ] AGENTS, architecture, data contract, roadmap and handover match current code.
- [ ] \`SECURITY.md\` gives a safe disclosure route.
- [ ] \`CONTRIBUTING.md\` and PR template are actionable.
- [ ] Packaging metadata and licence legally reviewed by owner.
- [ ] Dependency audit and minimal permissions documented.
- [ ] Release note/changelog accurately lists supported features and known gaps.
- [ ] Migration provenance credited; no unrelated concept assets copied.
- [ ] SemVer strategy and version bump approved.
- [ ] Repository About description/topics and default branch checked.

## Release decision record

| Item | Value |
| --- | --- |
| Current intended status | Experimental / pre-alpha |
| Current version field | \`0.1.0.dev0\` |
| Automated baseline | 23 locally passing tests at migration time |
| Current source input | Synthetic v1 fixture |
| GitHub data collector | Not implemented |
| Public GitHub profile integration | Not installed |
| Owner design approval | Not yet given |
| Stable public release | Not authorised |

**If a gate cannot be validated**, leave it unchecked and state why. Never silently bypass or claim an unrun check passed.


## GitHub GraphQL calendar gate

- [ ] Verify read-only GitHub Actions GraphQL collection against a real public profile and preserve calendar/route provenance separation in the generated SVG.
- [ ] Check any anonymous restricted/private contribution count handling and profile visibility assumptions.
- [ ] Ensure missing query days are explicitly unknown, not displayed as authoritative zeros.
- [ ] Confirm GitHub calendar is never combined arithmetically with public event-ledger counts.
- [ ] Verify the fallback when no token is available is clearly labelled incomplete rather than presented as GitHub's contribution calendar.
