# Preserve fixed cuboid parameter observers after a Fusion save

The strict Fusion reader now checks both observed parameter search
observer orders for the fixed XY cuboid. The first entry must be
the parameter table. The remaining seven must be the exact table
parameters in creation order or ascending Design object identity.
Each observer retains its original rank and name binding. Strict
SDK and CLI JSON preserve the original typed order.

The existing cuboid constructor again uses only its authoring
classes. The saved face appearance class stays available through
the strict reader’s separate vocabulary. This preserves the
existing constructor and the styled cuboid reader together.

All 12 generated or vendor-saved archives passed strict SDK JSON.
All six edited and restored vendor saves passed the CLI with
`partial: false`, exact source digests and equal typed state.
Five malformed subject lists refused. Fusion 2706.1.17 passed the
12 geometry, history, edit and reopen stages for the three exact
generated archives. Presentation, viewport picking, previews and
generalized public writer admission remain open.

[Exact native and reader evidence](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#generated-cuboid-native-lifecycle-and-observers)
