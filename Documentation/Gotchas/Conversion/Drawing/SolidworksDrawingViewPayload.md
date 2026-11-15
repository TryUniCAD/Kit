# Drawing view payload doubles are not eight byte aligned

## Expectation

The `moView_c` payload is a sequence of doubles and integers, so each double
starts at an eight-byte boundary.

## Actual behavior

The payload starts with a one-byte prefix, so the first double starts at offset

1. The payload also carries a two-byte gap after the first vector and a
   three-byte gap after the second scale, so later doubles are not aligned either.

The payload is 124 bytes:

```
prefix      1 byte
origin      3 doubles
scale one   1 double
normal      3 doubles
gap one     2 bytes
scale two   1 double
gap two     3 bytes
flag        1 int32
value       1 double
zero        1 int32
index       1 byte
gap three   3 bytes
reserved    4 doubles
class ref   2 bytes
```

Reading the payload as eight aligned doubles gives `(0, 0, 0, -3.1e231, ...)`
instead of `(0, 0, 0, 1, 0, 0, 0, 1)`.

## Workaround

Read the prefix byte first, then read the doubles and integers at the offsets
above. `DefinitionView.ViewRecordAt` does this and rejects a record whose width
is not 124 bytes. `DefinitionSheet.SheetRecordAt` reads the sheet block the same
way, including its leading class reference.

## Evidence

`ViewBlock` and `EncodeViewBlock` reproduce the `moView_c` bytes for all ten
tracked drawings. The first record is `*Full Sheet` with origin `(0, 0, 0)`,
scale one `1.0`, normal `(0, 0, 0)`, scale two `1.0`, flag `-1`, value `-1.0`,
and index `0`.
