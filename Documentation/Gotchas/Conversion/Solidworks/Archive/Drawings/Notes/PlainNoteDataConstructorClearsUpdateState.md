# Plain note data clears the initial node update state

The generic node constructor starts `f0c=1`. Fresh note data immediately takes a different sequence: its detail-item base calls `setNeedsUpdate(state=0, enabled=1, source=null)`, leaving serialized `f0c=0`.

The existing SDK generic node initializer also admits anonymous names only for its declared plane/configuration classes. Reusing it unchanged for note data either rejects the node or preserves the wrong initial update word. Keep the actual anonymous note-data initialization and state-zero operation explicit; do not import a saved flag word.

The [complete native constructor and mask proof](../../../../../../../re/solidworks/records/DrawingPlainNoteConstruction2026.md) records the fields and exclusions. This is a constructor fact, with later registration and native note acceptance still separate.
