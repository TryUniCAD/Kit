# Lock unseen principal sketch frames before writer correction

The [profile transform trace](../../../../../re/solidworks/records/ProfileTransformDirection2026.md)
identified the stored model-to-sketch direction. The current research writer
uses its inverse for the nonidentity principal frames. A native rebuild can
still succeed, so the next evaluation must inspect the generated archive field
before opening the file, as well as measure the edited native result.

The [new source specifications](../../../../../re/tooling/sw2026/FrameSourceSpecs.json)
reserve a Top-plane diameter boss and a Right-plane radial boss with distinct
geometry, directions and poses. The existing independent native author runs
each in a fresh process and locks its save after a fresh reopen and healthy
controls. Only the lock leaves the source side until a corrected writer is
frozen and remote predictions and transform checks pass.

This defines an unmeasured cohort. The previous measured files stay associated
with their original writer revisions. Displaced planes and arbitrary sketch
frames need separate source families.
