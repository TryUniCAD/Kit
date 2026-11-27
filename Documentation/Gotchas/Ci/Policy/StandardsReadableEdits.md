# Readable standards require explicit provenance edits

## Expectation

A branding correction in a preserved standards page should retain the original policy and its provenance.

## Actual behavior

The preservation workflow compares each readable copy with the exact content of its pinned historical source.
A direct branding edit fails that comparison even when the underlying policy is unchanged.

## Workaround

Keep the historical source commit, blob, hash, size, and inventory unchanged.
Record each approved readable-text change as a byte range and replacement in `Manifest.json`.
The workflow verifies the original source first, then applies the explicit edits before comparing the readable copy.
Apply ranges in reverse order so earlier offsets remain stable.
Pin the resulting text hashes and the edited-source inventory in the workflow.
The manifest alone cannot authorize a different transformation.
Review each readable-text diff whenever the pinned hashes change.

See [the workflow](../../../../.github/workflows/SteeringSync.yml),
[the manifest](../../../../.agents/skills/standard-pr-practice/references/Standards/Manifest.json),
and [the attribution change](../../../Changes/Policy/ProjectAttribution.md).
