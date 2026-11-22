# Read the active body of a saved SOLIDWORKS width-depth part

The strict part reader binds the selected native body to its editable
history for the measured Front Plane rectangular blind boss whose depth
follows half the sketch width. It checks the actual active partition,
body atom, producing feature and outward boundary against the live
parameters. The full read exposes the linked B-rep. Use
`include_brep=False` to retain the editable history, body identity and
measures without exposing geometry or Parasolid attachments.

The disclosed SOLIDWORKS 2026 SP05.2 save passes both read modes and
matches its earlier native volume, area and centre to six significant
figures. Three cold and saved controls preserve their complete neutral
JSON digests. A foreign cache and crossed creator refuse in both modes.
The saved text property scope remains unresolved. This change adds a
reader path only. [Proof receipt](../../../../../re/solidworks/measurements/2026/SdkSavedWidthDepth01.json)
