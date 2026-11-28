# Fusion can reject renaming a new root component

The saved-cuboid control used the licensed Fusion 2706.1.17 public API to
create a new unsaved design. Assigning a name to `design.rootComponent.name`
raised `3 : root component name cannot be changed` before the sketch was
created. The batch recorded zero documents before and after cleanup. Its
failed capture receipt SHA-256 is
`1de7dc789065cbe720109bd4702770829d8890f2bf006324eedb29433777cefb`.

Leave the root's name assigned by Fusion when authoring a local control.
Use the declared sketch, feature and body names for the model and the local
archive file name to identify the case. This preserves the intended
control geometry and face roles.

[Saved cuboid control procedure](../../../../../re/Fusion/LocalOracle/SavedCuboidRoundTrip/README.md)
