# Design-only imported pocket reads still need the physical owner

An imported feature entry can exist while the SDK reports a generic body
with zero faces and no named producer. Before strict pocket readback,
skipping Parasolid payload collection caused this result in the design-only
view of two exact generated parts. Full reads of those files also refused
their linked interior trim.

Validate the selected local body against its active configuration and
feature first. Project the validated body identity and counts before
omitting geometry and payloads from the design-only result. A foreign
storage group or a competing payload still refuses.
[Exact readback evidence](../../../../../re/solidworks/records/LocalPocketTopology2026.md#strict-sdk-readback)
