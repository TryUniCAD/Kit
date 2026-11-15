# Drawing units and line style blocks are not self describing

## Expectation

The `Contents/Definition` units and line style blocks are length-prefixed
records, so a reader can walk them without knowing the block boundaries.

## Actual behavior

The units block starts with a four-byte entry count and 16-byte entries, but
the remaining tail has no length prefix and its size depends on the unit kind.
The length block tail is 96 bytes, the angle block tail is 28 bytes, and the
number block tail is 26 bytes. The tail carries the paper width and other
constants that are not yet interpreted.

The line style block is a sequence of records with no outer count. Each record
ends with a one-byte terminator. A zero terminator is followed by a two-byte
class reference and another record; a one terminator ends the block. The class
reference varies across drawings (`0x811f`, `0x8238`, `0x8226` in the tracked
corpus), so it cannot be treated as a constant separator.

## Workaround

Read the units block with `UnitTableAt`, which uses the leading count and the
fixed 16-byte entry width, and preserve the remaining bytes as `Tail`. Read the
line style block with `LineStyles`, which follows the terminator to decide
whether a class reference follows. `EncodeUnitTable` and `EncodeStyles` write
the preserved values back byte-exactly.

## Evidence

`UnitTableAt` and `EncodeUnitTable` reproduce every units block, and
`LineStyles` and `EncodeStyles` reproduce the `moLineStyle_c` block, for all
twelve tracked drawings under `re/solidworks/examples/Drawings`.
