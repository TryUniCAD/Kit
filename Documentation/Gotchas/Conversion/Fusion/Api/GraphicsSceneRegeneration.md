# Fusion can regenerate a styled cuboid viewport without a saved OGS scene

A saved face appearance can appear to depend on the OGS world and
mesh stream because they also refer to the attached material. The
exact top-red control reopened in Fusion 2706.1.17 with identical
camera, visibility, face sources, colors and pixel bytes after
removing only the OGS subtree from the same archive. The Design
and journal kept the actual face appearance assignment.

Use same-source, repacked and OGS-omission controls before treating
scene data as optional for another profile. Measure the loaded
viewport before fit or rebuild, and verify picking, previews and
the edit-and-save lifecycle separately. A structural scene that
passed Kit’s wire readback stalled in Fusion during import.
[Exact scene comparison](../../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#native-scene-omission)
