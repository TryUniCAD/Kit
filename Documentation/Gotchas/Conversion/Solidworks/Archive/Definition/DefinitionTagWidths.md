# Definition replay requires canonical tag widths

## Expectation

A decoded archive tag supplies enough information to reproduce its original bytes.

## Actual behavior

The native tag loader can read a six-byte escaped reference to a small map
index. The writer emits the same class or object reference in two bytes.
Escaped zero likewise decodes as null and emits as a two-byte null tag.
[Native tag rules](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/ArchiveTagGrammar2026.md)

## Workaround

The bounded ordinary part Definition reader compares the physical tag width
with the canonical writer width before advancing its cursor or applying the
tag to the map. Canonical wide references still work at the native threshold.
Other graph readers retain their current tag policy. [Process cases](../../../../../../tests/Convert/Solidworks/ArchiveDefinition/DefGuardTests.py)
