# Lock unseen principal sketch frames before writer correction

The [profile transform trace](../../../../../re/solidworks/records/ProfileTransformDirection2026.md)
identified the stored model-to-sketch direction. The earlier research writer
used its inverse for the nonidentity principal frames. A native rebuild can
still succeed, so the next evaluation must inspect the generated archive field
before opening the file, as well as measure the edited native result.

The [new source specifications](../../../../../re/tooling/sw2026/FrameSourceSpecs.json)
reserve a Top-plane diameter boss and a Right-plane radial boss with distinct
geometry, directions and poses. The existing independent native author runs
each in a fresh process and locks its save after a fresh reopen and healthy
controls. Only the lock leaves the source side until a corrected writer is
frozen and remote predictions and transform checks pass.

The [source lock](../../../../../re/solidworks/v2026/heldout/FrameSourceLock.json)
binds both native files before the writer change. The
[source completion receipt](../../../../../re/solidworks/measurements/2026/FrameSourceCompletion01.json)
records four fresh source phases, 192 checks, healthy bracketing controls,
unchanged source/control hashes and unchanged licensing process IDs. Private
API observations and original payloads remain sealed. This qualifies the
source design, with no new writer result.

Previous measured files stay associated with their original writer revisions.
Displaced planes and arbitrary sketch frames need separate source families.
