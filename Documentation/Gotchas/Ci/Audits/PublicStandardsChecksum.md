# Public standards checksums can look like credentials

## Expectation

A public SHA-256 in a preserved standards map should be recognized as integrity metadata.

## Actual behavior

Gitleaks `8.30.1` associates `Token` in a standards filename with the adjacent high-entropy checksum.
It reports `generic-api-key` at `.github/workflows/SteeringSync.yml:102` on both rejected PR #253 queue candidates.
The value is the independently derived digest of the readable historical standard, not a service credential.
See [the redacted scanner job](https://github.com/TryUniCAD/Kit/actions/runs/45063182858/job/137333436895).

## Workaround

Classify only that exact public value at the anchored workflow path under the matching detector rule.
Keep the full-history scan and all other rules enabled.
Run real scanner controls proving that the value elsewhere and an unknown value at that path remain detectable.
Do not exempt the workflow or arbitrary hexadecimal values.

See [the repair](../../../Changes/Ci/AttributionQueueRepair.md).
