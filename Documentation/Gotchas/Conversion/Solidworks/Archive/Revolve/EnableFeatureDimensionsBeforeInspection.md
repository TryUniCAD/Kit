# Enable feature dimensions before inspecting a revolve

The revolve oracle locates a driving parameter through the feature's display
dimensions. The document's `swDisplayFeatureDimensions` setting controls the
feature-dimension display filter. An inspection that depends on the display
collection needs to account for that setting before recording a missing
angular display. [SOLIDWORKS detailing preferences](https://help.solidworks.com/2024/english/api/swconst/DP_Detailing.htm)

Resolve the setting's identifier from the installed SOLIDWORKS 2026 type
library. Read its current value, enable it for the in-memory inspection, and
restore the original value before closing the document. Verify the source
digest after the probe. A 360-degree case with no observable display still
needs separate evidence for the expected parameter layout and edit path.
See the [revolved boss source procedure](../../../../../../re/solidworks/records/OrdinaryRevolvedBoss2026.md).
