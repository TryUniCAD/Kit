# A DWG without its four header shorts stalls the drawing open

The DWG header section of a Fusion drawing ends with four BS values after its handle stream.
Each value uses the 2-bit `00` code and a full 16-bit short, unless it is below 256.
A BL value follows, then fill bits from the `0x55` pattern.
Every Fusion save writes that BL as zero, with the 2-bit `10` code.
The ODA specification lists four unknown BS values at the end of the header variables.

Kit reads these bits as `TailWidth` and `TailBits` and, since the tail was solved, writes them from
the header content instead of copying them.

| DWG                                         | `TailWidth` | Four values                       | BL and fill |
| ------------------------------------------- | ----------- | --------------------------------- | ----------- |
| A1 control                                  | 77          | `0x8DA9`, `0xC9A5`, `0xF093`, `0xFED8` | `10` and `101` |
| A2 control                                  | 77          | `0x7B4C`, `0xCEEE`, `0x05E7`, `0x8C61` | `10` and `101` |
| 27 DWG exports of Fusion 2706.1.17          | 77          | Different in every export         | `10` and `101` |
| Export of `U9OwnShortsZeroPad`              | 101         | Different                         | Full BL and `101` |

`U9OwnShortsZeroPad` had zero fill bits, so Fusion read a BL with the `00` code there.
Its export wrote that BL back with a full 32-bit value.

The values do not follow from the DWG content alone.
`H1NoAcm` and `N2AuthoredF2d` carry the same DWG bytes.
Their Fusion exports still carry unrelated values, such as `0xBB79` and `0x1341` first.

Variants without the values stalled.

| Variant            | Header tail                                    | Result                                        |
| ------------------ | ---------------------------------------------- | --------------------------------------------- |
| `Q1NoDataStore`    | The A1 values and fill                         | Opened in 4.7 s with 3 views and 1 dimension  |
| `U1ZeroShorts`     | `Q1NoDataStore` with four zero values (`10` code) and zero fill | Not open after 453 s, no dialog |
| `F7ZeroHeaderTail` | The A1 control with no values and zero fill    | Not open after more than 10 minutes           |

Fusion checks the values themselves.
These variants change only the header tail of `Q1NoDataStore`.

| Variant              | Header tail                                         | Result                          |
| -------------------- | --------------------------------------------------- | ------------------------------- |
| `U9OwnShortsZeroPad` | The A1 values with zero fill bits                   | Opened in 3.3 s                 |
| `B10FifthLong`       | The A1 values with the BL set to 1                  | Opened in 3.5 s                 |
| `W2KitShorts`        | Four full values that Kit takes from the version GUID | Not open after 185 s, no dialog |
| `U2ForeignTail`      | The 77 tail bits of the A2 control                  | Not open after 181 s, no dialog |

## What the values depend on

Each variant below keeps the A1 values and changes one input.
A stall means that the values depend on that input.

| Variant              | Input changed                                       | Result                     |
| -------------------- | --------------------------------------------------- | -------------------------- |
| `H1NoAcm`            | Objects: AutoCAD Mechanical objects and unused blocks removed, handle map rebuilt | Opened |
| `Q1NoDataStore`      | Objects and sections: data-store flags and section removed | Opened in 4.7 s     |
| `B0Base`             | `Q1NoDataStore` emitted again in a new bundle       | Opened in 4.4 s            |
| `Q8AuthoredSections` | Section set and section ids                         | Opened in 5.2 s            |
| `W3KitAuxHeader`     | Auxiliary header                                    | Opened in 3.5 s            |
| `W4KitSummary`       | Summary                                             | Opened in 3.4 s            |
| `W5KitFreeSpace`     | Object free-space record                            | Opened in 6.1 s            |
| `W6KitClassCounts`   | Class instance counts                               | Opened in 3.6 s            |
| `N2AuthoredF2d`      | Every F2D member, with a new DWG member name        | Opened in 4.3 s            |
| `B8UserReal`         | `USERR4` from 0.0 to 1.0, the same in every save    | Not open after 61 s        |
| `B1VersionGuid`      | `VERSIONGUID`, a header string                      | Not open after 61 s        |
| `B9AllVaried`        | Every header variable that differs between saves    | Not open after 61 s        |

The values therefore cover the header variables, both the data and the strings.
They cover neither the objects nor the other sections.
A single changed header variable breaks them, so the variables that differ between saves were not tested one by one.

## Ruled-out rules

The values are not a plain checksum of the header.
These functions were tested on 31 Fusion saves: the A0, A1 and A2 controls, the historical example and 27 exports.

| Inputs                                                           | Functions                                    | Matches |
| ---------------------------------------------------------------- | -------------------------------------------- | ------- |
| Header bytes before the tail, with and without sentinel and size | CRC-16 ARC, Kermit, CCITT and Buypass        | None    |
| Same, with the tail bits set to zero                             | The same CRC-16 functions                    | None    |
| Header data and strings, and the handle stream, as packed bits   | The same CRC-16 functions                    | None    |
| Every input above                                                | Seeds 0, `0xFFFF`, `0xC0C1` and each of the four values | None |
| Every input above                                                | CRC-32, CRC-32C and CRC-32/MPEG-2, seeded with 0, all ones or two of the values | None |
| Every input above                                                | Adler-32, CRC-64 ECMA and ISO                | None    |
| Every input above                                                | Any four adjacent words of MD5, SHA-1, SHA-256, SHA-512 and BLAKE2b | None |
| Three of the four values                                         | CRC-16 of the other three, in any order      | None    |
| Save times, handle seed and GUID words as seeds                  | MSVC, Park-Miller, `lrand48` and MT19937 sequences | None |

Earlier runs also ruled out CRC-16, CRC-32, Adler-32 and digests over each section, the header area and the whole file.
The values match no word of the fingerprint GUID, the version GUID or the save timestamps.
They do not appear elsewhere in the DWG as aligned bytes or as typed object values.
Their bits are evenly spread, and the four values show no relation to each other.

The values therefore behave like a keyed check over the header variables.
Only Fusion's own code could show the key or the rule, and that code is out of scope.

## The rule

The four values are one encrypted 8-byte block, not four independent values.

The plaintext is four little-endian shorts: a 16-bit checksum, the product code `1`, the writing
version code, and zero. Fusion 2706.1.17 writes version code `26` for both `AC1027` and `AC1032`;
seventeen of the twenty-two `AC1032` corpus saves use it too.
The cipher is Blowfish with the standard constant table, so the P-array and the four S-boxes are the
first 1042 words of the fractional part of pi.
The 16-byte key is a constant in the `libacdb` data of `AcCoreConsole.app`, not a value taken from
any document.
The module that holds both is
[`TailCipher`](../../../../../src/convert/formats/Fusion/DrawingCodec/Dwg/Integrity/TailCipher.py).
Each encrypted short goes into the file as a 2-bit `00` prefix and the 16 bits big-endian, so the
four shorts are 72 bits and the remaining bits of the 77 are the `0x55` fill.

The checksum is the low 16 bits of a 32-bit sum. It runs from the first bit of the header area, which
is the area size field, to the first bit of the tail. Each item is a CInt16 read with a 2-bit code in
MSB-first order:

| Code | Width | Value                       |
| ---- | ----- | --------------------------- |
| `00` | 16    | the 16 bits little-endian   |
| `01` | 8     | the 8 bits                  |
| `10` | 2     | `0`                         |
| `11` | 2     | `0x100`                     |

An item that runs past the end contributes nothing.
The module that holds the sum is
[`HeaderChecksum`](../../../../../src/convert/formats/Fusion/DrawingCodec/Dwg/Integrity/HeaderChecksum.py).

Three details made the rule hard to see.

* The 16-bit read is alignment dependent. At a zero bit offset the native reader uses a little-endian
  `ldrh`; at any other offset it assembles the two bytes MSB-first. The checksum consumes both, so a
  decoder that is fully big-endian or fully little-endian matches neither.
* The sum is 24 bits in practice and only its low 16 bits are checked. Comparing a 32-bit sum against
  the stored value hides the match.
* The area size field in the header is the header bit size, while the sum ends at the tail. They are
  different numbers; for one control the size is 6075 bits and the sum ends at bit 6707.

## Evidence

Kit's writer now computes the tail from the header content.
Re-emitting a Fusion-saved header reproduces the stored bytes exactly for 54 of the 60 corpus saves:
all 38 `AC1027` saves except `U9OwnShortsZeroPad`, and 17 of the 22 `AC1032` saves.

The six that differ are the corpus rows with a non-standard tail, not writer mistakes:

| Save                                  | Tail width | Why it differs                                       |
| ------------------------------------- | ---------- | ---------------------------------------------------- |
| `U9OwnShortsZeroPad`                  | 101        | Crafted with a fifth value, so its plaintext is not this block |
| `U1SheetOnly`, `U3ThreeViews`, `U5SheetDimension` | 13 | Corpus rows whose tail region is not four shorts |
| `V3ThreeViews`, `V5SheetDimension`    | 77         | The stored block does not decrypt to a plaintext with product `1` and version `26` |

Fusion's own reader agrees with the computed values. A Kit-authored `AC1032` drawing whose header was
computed and not copied opened in Fusion 2706.1.17 with three sheets, views `5, 4, 4` and one
dimension, and Fusion applied an edit to it: a view scale of 4.0 became 2.0 and the document reported
itself modified.

## What Kit does

Kit writes the tail from the checksum and the cipher, and never copies a tail from a saved file.
A version without a known version code raises `ValueError` instead of writing a guess.
The [authored shell gotcha](FusionDrawingAuthoredShell.md) still applies to the pre-solved saves it
records.
