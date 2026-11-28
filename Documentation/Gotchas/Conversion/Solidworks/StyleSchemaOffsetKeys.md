# Style schema offset keys have two spellings

Native offsets do not determine the Python dictionary key spelling. In the
current `ConfigDetail.py` schema, the `ints`, `dbls` and `bytes_` helpers format
an offset with `f"f{offset:x}"`, producing `f8` and `fc`. Explicit schema
declarations sometimes use `f08` and `f0c` instead. Both conventions exist in
the same style graph.

The first remote process check reached `moDimDefs_c` inside the new detail
graph and failed on missing `f8`; its builder supplied `f08`. A complete static
audit also found the base annotation, base dimension, label base/root, note
helper and datum-feature helper variants. Their builders now match each exact
schema declaration. Character formats, unit records and the detail root retain
their explicitly padded names. Do not normalize the entire object tree or
silently accept either spelling: that would conceal a field-key error.

The mismatch is in the Python record interface, not additional bytes in the
native grammar. Native field ownership and construction evidence remain in the
[construction record](../../../../re/solidworks/records/StyleConstruction2026.md).
