# Computed DWG header tail

## Problem

A DWG header section ends with four 16-bit values that Fusion checks before it opens a drawing.
Saves written without them stall the open in Fusion 2706.1.17 with no dialog, as the
[header tail gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) recorded.

Kit read the bits and wrote them back, so an authored DWG could not be loaded by Fusion unless the
values were copied from a Fusion save. Copying them is donor data, and it makes the writer dependent
on one document.

## Change

Kit now computes the four values from the header content.

| Module                                                                                                      | Role                                                       |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [`HeaderChecksum`](../../../../src/convert/formats/Fusion/DrawingCodec/Dwg/Integrity/HeaderChecksum.py)      | 32-bit sum of CInt16 items over the header area, low 16 bits |
| [`TailCipher`](../../../../src/convert/formats/Fusion/DrawingCodec/Dwg/Integrity/TailCipher.py)              | Blowfish with pi-derived constants and the product key     |
| [`EmitHeaderVars`](../../../../src/convert/formats/Fusion/DrawingCodec/Dwg/Header/EmitHeaderVars.py)         | writes the encrypted tail instead of the stored tail bits  |

The plaintext is four little-endian shorts: the checksum, the product code `1`, the version code and
zero. The encrypted shorts are written as a 2-bit `00` prefix and 16 bits big-endian each, then the
`0x55` fill to the byte boundary.

`TailCipher` derives the P-array and the four S-boxes from the fractional part of pi with `Decimal`,
so no cipher table is stored. The only constants are the 16-byte product key and the pi generator.

The version code is `26` for `AC1027` and `AC1032`. A version with no known code raises `ValueError`
rather than writing a guess.

This is an encrypted product code and version, not a vendor signature.
The comment Kit writes stays `This file was last saved by Kit.`

## Verification

Re-emitting a Fusion-saved header reproduces the stored bytes exactly for 54 of the 60 corpus saves:
37 of 38 `AC1027` and 17 of 22 `AC1032`. The six that differ are the corpus rows with a non-standard
tail, which the gotcha lists.

A Kit-authored `AC1032` drawing whose header was computed opened in Fusion 2706.1.17 with three
sheets, views `5, 4, 4` and one dimension.
Fusion then applied an edit: a view scale of 4.0 became 2.0 and the document reported itself modified.

An untouched copy of the source bytes was opened through the same path as a control.
It produced the same open and edit results, so the numbers above come from the file and not from a
copy of the source.

## Tests

`tests/convert/formats/FusionCodec/Drawings/DwgAuthorTests.py` now decrypts the authored tail and
asserts the product code, the version code and the reserved short instead of comparing placeholder
values.

`tests/convert/formats/FusionCodec/Drawings/DwgHeaderTailTests.py` adds three boundary checks on the
author and reader:

* an authored header types, and its stored tail is at least 72 bits with no bits above them.
* repairing the header CRC and changing nothing else still types.
* changing one tail bit and repairing the CRC makes the header fail to type.

The third check is the important one. The CRC covers the tail, so a reader that ignored the checksum
would still accept the tampered file once the CRC is repaired.

## Limits

The writer raises for a version without a known version code, so a future DWG version needs a new code
before Kit can write it.

The product key comes from the `libacdb` data of the Fusion console that reads the drawing.
A Fusion release that changes the key would need the key updated; the checksum and the encoding would
not change.
