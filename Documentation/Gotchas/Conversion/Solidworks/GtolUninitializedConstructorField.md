# GTol constructor leaves one serialized field unset

An empty helper constructor might be expected to initialize every current wire
field. In 2026 `sldmfcu.dll`, `moGTolDataHelper_c` constructor `0x3c7d1b50` does
not assign field `f80`. Its current serializer `0x3c85ce50` nevertheless writes
that field as an unsigned byte. Owner load/store methods `0x3c7db630` and
`0x3c7dc8f0` only call copy `0x3c7d76b0`, which preserves the field.

The older-version reader fallback below `0x3751` also writes `f80=0`, but
that alone does not prove a fresh default. Trace the owning data projection.
In `sldmodu.dll`, native GTol-data constructor `0x4c7c5f80` explicitly zeroes
the qword at `+0x248`, including the integer member at `+0x24c`.
Projection `0x4c7d2930` reads that member at instruction `0x4c7d3648` and
writes helper `+0x80` at `0x4c7d3653`. Its absent-data branch also selects
zero. Reverse application `0x4c7d04a0` maps the helper back to data `+0x24c`.

The research builder's zero is therefore derived from native fresh GTol data,
not the helper constructor or captured save. Its user-facing mode name and
nonzero modes remain unresolved. A held-out vendor check of the assembled
candidate is still required before production acceptance. Do not copy the byte
from a saved part or silently classify an uninitialized field as a format constant.

Binary identity and the complete construction scope are in the
[2026 construction record](../../../../re/solidworks/records/StyleConstruction2026.md).
