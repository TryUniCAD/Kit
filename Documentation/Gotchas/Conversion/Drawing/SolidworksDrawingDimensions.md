# Drawing dimension records are not a flat parameter list

## Expectation

A drawing dimension should be a small record with a name, a value, and a
placement, so a reader can decode it from the `Contents/Definition` stream
without knowing the dimension kind.

## Actual behavior

Dimensions appear as several sibling class declarations, not one record. In
`coincident.SLDDRW` the angular dimension is `sgAnglDim` (a four-byte zero
value), then `moAngleParameter_c` (a 76-byte parameter record), then
`sgLineHandle` (3,628 bytes of leader geometry). The offset dimension is
`sgSkOffsetDim`, whose value block is 49,488 bytes and contains only two `D1`
strings plus a large binary payload.

The `moAngleParameter_c` record is stable across `coincident`, `large`, and
`multisheet`:

- class reference (two bytes, `0x8065` or `0x8051`)
- name string (`D2`)
- value double (`2.0`)
- flag int32 (`-1`)
- unit int32 (`0`)
- text string (empty)
- two zero bytes
- measured double (`1.3446183501864888`, about 77.04 degrees)
- three zero bytes
- one byte (`0x29`)
- twenty zero bytes
- count int32 (`2`)
- eight trailing bytes

The `sgSkOffsetDim` first record has the same shape with name `D1`, value
`2.0`, and measured `0.0127` (12.7 mm), but the block then continues with a
second `D1` record and a large payload that is not a parameter list.

## Workaround

Do not treat the dimension blocks as a flat list. Read `moAngleParameter_c`
with the fixed layout above and preserve the remaining bytes. The
`sgLineHandle` and `sgSkOffsetDim` payloads are not decoded; a caller that
needs them must keep the source container.

## Evidence

The `moAngleParameter_c` layout was checked against `coincident.SLDDRW`,
`large.SLDDRW`, and `multisheet.SLDDRW` under
`re/solidworks/examples/Drawings`. The measured double is identical in all
three, and the class reference differs only between `0x8065` and `0x8051`.
