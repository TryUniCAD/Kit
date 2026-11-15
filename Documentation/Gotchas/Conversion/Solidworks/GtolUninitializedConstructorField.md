# GTol constructor leaves one serialized field unset

An empty helper constructor might be expected to initialize every current wire
field. In 2026 `sldmfcu.dll`, `moGTolDataHelper_c` constructor `0x3c7d1b50` does
not assign field `f80`. Its current serializer `0x3c85ce50` nevertheless writes
that field as an unsigned byte. Owner load/store methods `0x3c7db630` and
`0x3c7dc8f0` only call copy `0x3c7d76b0`, which preserves the field.

The same 2026 reader explicitly initializes `f80=0` for versions below
`0x3751`. The fresh research style builder uses that documented compatibility
seed for the unused helper and records the weaker evidence classification.
It does not claim this is a constructor default or that the application role
is fully understood. A held-out vendor check of the assembled candidate remains
required before production acceptance. Do not copy the byte from a saved part
or silently classify an uninitialized field as a format constant.

Binary identity and the complete construction scope are in the
[2026 construction record](../../../../re/solidworks/records/StyleConstruction2026.md).
