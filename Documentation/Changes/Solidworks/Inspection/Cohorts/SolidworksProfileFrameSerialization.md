# Store the model-to-sketch transform in generated profiles

The research writer now transposes the rigid sketch placement and maps the
model origin into sketch space before serializing `pd_ff0`. That is the
direction stored by SOLIDWORKS 2026. The previous output used the world
placement directly; identity hid the error on Front, but Right and Top have
different forward and inverse matrices. The [field trace and native
measurements](../../../../../re/solidworks/records/ProfileTransformDirection2026.md)
establish which transform the profile owns.

The fresh construction processes expose the decoded persisted matrix,
translation and scale. The pinned comparison continues to require exact
historical hashes. For current output it requires the expected model-to-sketch
values, complete Front file identity and only a `Config-0-ResolvedFeatures`
payload change on Right and Top. Stream order and uncompressed sizes must
remain unchanged. The existing native measurements stay attached to the
previous emitter hashes.

The [independent source lock](../../../../../re/solidworks/v2026/heldout/FrameSourceLock.json)
predates the correction. New native acceptance requires testing predictions
from the corrected frozen emitter against those sources. Displaced planes
and arbitrary frames are outside this change's measured scope. The public
adapter remains read-only.
