# Stored tolerances in rectangular imported solids

Strict SOLIDWORKS part reads accept the measured rectangular local-body
save layout. Kit checks the selected configuration, live import feature,
kernel body and rollback mark. It returns the complete solid, the six
stored face tolerances and the native body's name. Edge and vertex
tolerances appear unset when the saved cells carry the native missing
value.

The internal box constructor also accepts one positive uniform
tolerance supplied by the neutral faces, edges and vertices. It
encodes the length in their typed Parasolid cells during construction.
Two guarded builds reproduce both previously native-tested complete
parts. The strict reader recovers both corresponding native saves
and matches their geometry to the prior native measurements.

[Construction and readback evidence](../../../../../re/solidworks/records/OwnedBoxTolerance2026.md)
