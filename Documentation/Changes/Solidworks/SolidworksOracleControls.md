# SOLIDWORKS polygon source controls

The native-format research now records an immutable source lock for three
polygon extrusions and two rectangular controls authored in SOLIDWORKS 2026
SP05.2. The lock precedes the polygon family emitter and records that lower-level
constructor and archive helpers already existed.

Use [the lock](../../../re/solidworks/v2026/heldout/polygon/Lock.json) for source
identity, neutral specifications and measured geometry. The native files remain
in the private research store and must not supply output fields or runtime data.

Actual authoring evidence: all five files saved with no save error or warning
and one solid body. The two controls agree on volume, area and centre of mass.
The original per-feature error queries were unavailable because the harness used
the wrong out-parameter type. No zero-error rebuild acceptance or generated
output acceptance is claimed. No tests ran locally.

The [adapter guide](../../Reference/Adapters/Solidworks.md) continues to describe
SOLIDWORKS as read-only until fresh output satisfies every CAD success criterion.
