# System folders have model bindings

## Expectation

Creating a folder object and listing it among resolved features fully attaches
the corresponding native system node.

## Actual behavior

The 2026 folder `addToModel` callbacks also assign owning-model cache pointers.
The environment folder occupies model `0x1e0`, which is serialized in Config;
the same object can also appear in the resolved system-feature stream.
Other callbacks establish the document, comment, sensor, favorite, selection
and history folder caches. Body-folder getters use model `0x1500/0x1508`.
The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
lists exact callback and getter addresses.

## Workaround

Build the actual folder graph with an owning part and retain these object
relationships. Bind Config `f1e0` to the same environment object used by the
resolved graph. Carry the shared archive map between streams so its aliases
derive from traversal instead of copied or estimated indices.

Keep folder names and the requested feature order authored. Native UI insertion
callbacks have separate ordering policies; a class-list observation from one
template does not establish a universal default graph. Whole-file native
acceptance remains required after these construction relationships are closed.
