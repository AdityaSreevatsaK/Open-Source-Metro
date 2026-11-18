# Security policy

## Status

Open Source Metro is a **pre-alpha local SVG renderer**. It currently has no hosted service, no GitHub account integration, no live API collector and no private-data access. That reduces operational exposure but does not remove risks in untrusted JSON or generated SVG.

## Responsible reporting

Please avoid posting secret-bearing data, executable payloads, private repository URLs or exploit details in a public issue. Where available, use GitHub's **“Report a vulnerability”** / private security advisory feature for this repository. If private reporting is not enabled, contact the repository owner through an existing trusted channel and request a private disclosure method; do not post sensitive information publicly.

Do not assume a rapid-response SLA or a formal security team; this is an experimental project.

## Supported versions

No stable versions are currently supported. The latest \`master\` is the experimental development version. Security fixes should be proposed against the current source without claiming production support.

## Threat model

- **Untrusted source snapshots:** malformed schema, invalid timestamps, huge counts, duplicated/conflicting event IDs, control/Unicode direction chars and unknown repositories.
- **SVG/XML output:** hostile labels, links, attributes, embedded scripts/foreign objects or data URLs.
- **Provenance:** artificial contributions presented as genuine achievements.
- **Confidentiality:** accidental disclosure of private repository metadata, real account activity, secret tokens or connected-account exports.
- **CI:** untrusted PR code should not access elevated secrets or write permissions.

Current defensive measures:
- Strict v1 schema checks and UTC timestamps.
- Bounded strings/counts and safe GitHub HTTPS URL restrictions.
- Conflicting duplicate detection and XML escaping.
- Demo-only synthetic activity expansion.
- No network, token or external script dependency in renderer.
- GitHub Actions workflow uses \`contents: read\` and no credentials.

## Operational practices

1. Never paste access tokens into JSON snapshots, environment-independent examples or generated SVGs.
2. Keep any future \`GITHUB_TOKEN\` read-only, optional and local to the user's environment.
3. Default a future collector to **public data only** and document coverage gaps.
4. Review dependencies before adding them. Baseline runtime is standard library.
5. Run all tests and SVG reproducibility comparison before a change reaches default branch.
6. If a vulnerability is found, stop publication and document which versions or outputs are affected.

See [Data contract](docs/DATA_CONTRACT.md), [Architecture](docs/ARCHITECTURE.md) and [Release checklist](docs/RELEASE_CHECKLIST.md) for further guidance.
