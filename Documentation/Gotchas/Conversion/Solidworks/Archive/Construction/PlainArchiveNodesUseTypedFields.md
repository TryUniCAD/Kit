# Plain archive nodes use typed fields

The SDK construction primitives return `ArchiveNode` objects with `ClassValue` and `FieldsValue`.
The research `Obj` subclass also provides `cls`, `f`, `get` and subscript access.
Some existing research dimension checks require that subclass explicitly.

A direct early delegation can therefore fail before the shared SDK serializer receives the graph.
Do not import the research class into production or loosen concrete object validation to hide the mismatch.
Use the typed node fields at the caller boundary.
If older builder operations still need their accessors, finish those operations before installing the SDK-owned nodes.

The [blind construction process](../../../../../../re/tooling/sw2026/SdkBlindEndProcess.py) uses this latter boundary.
It preserves the existing metadata construction and compares the actual generated native streams after the SDK replacement.
The [construction record](../../../../../../re/solidworks/records/SdkBlindEndConstruction2026.md) states the remaining caller ownership.
