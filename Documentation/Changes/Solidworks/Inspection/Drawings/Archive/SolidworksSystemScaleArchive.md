# System-scale archive codec

The ordinary version-19000 linked/named drawing Definition codec now admits concrete schema-one `moScaleSysScale_c` objects with an explicitly empty body. Original native RTTI, table dispatch, runtime schema and a complete three-byte return function prove that no additional body bytes are serialized. Existing class tags, maps, aliases and surrounding profile guards are reused.

This changes raw typed read/store admission only. It adds no fresh scale constructor, implicit model/style default, public strict drawing support or writer registration. Unknown classes, other schemas and unsupported versions remain closed. The original held-out writer snapshot and verdict are unchanged.

The actual two disclosed original reads now stop at the next concrete owner, `moCompProfile_c` schema 1. Neither complete stream is admitted, so byte parity is not claimed. AST, Black and Ruff passed. Root independently replayed all 43 prior-profile workers on the frozen reader source; all passed and the source remained immutable. No test suite or native application ran in this implementation lane.

[Native rule and exact diagnostic boundary](../../../../../../re/solidworks/records/ScaleSystemArchive2026.md).
