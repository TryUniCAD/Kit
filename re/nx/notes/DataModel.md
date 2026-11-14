# Siemens NX native part data model

## Evidence boundary

This note describes the bytes observed in NX 2506 and in the public cadmpeg
format documentation. It separates confirmed container facts from unresolved
object-model and feature semantics. The production reader in
`src/convert/adapters/nx/` does not read files from this directory.

## Envelopes

NX saves the same part in two envelopes.

| Envelope             | Signature                 | Directory                                  | Geometry                                                         |
| -------------------- | ------------------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| SPLMSSTR             | `SPLMSSTR`                | `HEADER` and optional `FOOTER` path tables | zlib-compressed Parasolid streams inside `/Root/UG_PART/UG_PART` |
| Compound File Binary | `D0 CF 11 E0 A1 B1 1A E1` | OLE storage and stream tree                | clear Parasolid streams inside `UG_PART/UG_PART`                 |

The modern envelope uses little-endian directory fields and a 48-bit footer
offset. A `FOOTER` offset of `0xffffffffffff` means the `HEADER` table is the
complete directory. The root entry payload is the stable UUID
`611ec9b3-fa60-d111-8ad9-0800362fb302`; it is not a file range.

The header directory is followed by a reserved trailer before the first file
payload. The trailer stores an xxh32 seal, little-endian, at trailer offset
`0x21E`. The seal covers the header directory from the `HEADER` marker at
`0x19` through the seal field. The file ends with a second xxh32 value: the
footer fingerprint covers the footer directory.

Seven NX 2506 saves with different payload sizes and directory layouts matched
both formulas exactly. Rebuilding a directory therefore only requires
recomputing these two seals. The production writer does that for every rewrite,
including rewrites that change stream sizes and shift later offsets.

## Canonical part payload

`/Root/UG_PART/UG_PART` begins with a counted segment index of 12-byte rows:

```text
type_code:u32  subtype_code:u32  value:u32
```

Row ordinal 1 is `type_code=1`, `subtype_code=1`, and `value` is the payload
offset after the index. The index may end up to eleven bytes before a twelve
byte boundary; the row count is the aligned part. The index words name
object-model sections and compressed stream wrappers.

NX 2506 also saves parts with no compressed streams. Their payload holds only
the index and OM sections, and NX requires both the `UG_PART` payload and its
`UG_PART/ExternalReferences` stream. Fast-load streams, `qafmetadata`,
`part/attrs`, and the saved toggle stream can be one byte each in a loadable
part. Replacing the `ExternalReferences` stream with a one byte placeholder
fails with `Unexpected end of file`.

Every OM section starts with a 0x56 byte header: `OM 01 01`, version `10`,
a section type word, flag bytes, a timestamp, the product string, the saved part
name, a class count, two flag words, and three counts. The last 12 bytes of each
section hold a 96 bit digest, and the u32 at header offset `0x52` equals
`section_size - 12`. The type registry follows at `0x56` with variable framing:
`01 len name id[11]`, `03 len name id[1]`, and bare `len name` entries all
appear in one section. NX 2506 saved sections with class counts 214, 3, 6, and
2 for an empty part.

The public cadmpeg code is a decoder only: its `cadmpeg-codec-nx` crate parses
sections, registries, operation records, and expressions but exposes no writer
or serializer. Its section model (`TypeDefinition`, `FieldDefinition`,
`IndexedSection`) confirms the layered structure but does not provide encoding
rules for a new part. The registry framing observed above does not match the
`06 name_len:u16` class-record form in the prose, so the leading block is a
separate type or field declaration lane.

The OM sections themselves are not optional. Zeroing the index row that names
one section makes NX report `Internal error` (code 65) even though the section
bytes remain in the payload. A from-scratch author therefore has to emit every
indexed section, including the class registry and object records. That encoder
is the remaining authoring work; the index, stream set, and container seals are
already understood.

The trailing 12 bytes of each section are not validated. Zeroing that digest in
one section, or in all four, still loads in NX 2506 with `unloaded 0`. Zeroing
the registry and record bytes after the section header fails with `Bad size for
allocation request in Storage Manager` (code 902), and zeroing the header
counts fails with `Found bad saved pointer value in file` (code 580143). The
registry and record content is therefore required even for an empty part.

A research encoder now exists in `re/nx/tools/OmSection.py`. It parses and emits
each section as: 0x56-byte header, reference count byte, reference declarations
(`len=name+1, name, code`), the `0x01` terminator, class declarations with the
commodity tail (storage token, base token, eight-byte schema fingerprint,
reference token), the opaque middle lane, the record area, and the 12-byte
digest. Re-encoding all four sections of `empty.prt` reproduces the
`UG_PART` payload byte for byte, and a container built from the re-encoded
payload with placeholder auxiliary streams and recomputed seals loads in NX 2506
(`encoded_empty.prt`, `unloaded 0`).

The section header is dynamic: version and kind are big-endian, the platform
text is `x64/Windows NT`, the saved part name is length-prefixed, then eight
little-endian counts, a pointer, and a reference-count byte. Parsing those
fields makes the same encoder round-trip `empty.prt` and `variant400.prt`
section 3 exactly; variant sections with a separate record area still need the
record lane decoded.

The header pointer is preserved per section and is not `size - 12`: it is the
record-area offset, so the encoder stores and re-emits it. With that, all four
`empty.prt` sections and all five `variant400.prt` sections round-trip byte for
byte.

The record area in `empty.prt` starts with three little-endian control words,
then a product frame (`01 27` followed by `NX 2506.9120 - External User
Function` and a terminator), then `08 SYSTEM 00`, `41 00`, and the object lane.
The control words are `0x214`, `0x22f`, and `2` for the feature-history
section.

Replacing the product text `External User Function` with `Authored User
Function` (same length) in every section and rebuilding the container with
placeholder streams and recomputed seals loads in NX 2506 (`authored_text.prt`,
`unloaded 0`), so the record-area text lane is writable.

Truncating a class lane by even one entry fails: `empty.prt` section 3 has
nine classes and eight loads as corrupt (580044), section 1 has seventeen and
sixteen fails, section 2 has fourteen and thirteen fails. The full class table
is therefore referenced by the middle lanes, and a minimal hand-authored schema
cannot be produced by shortening an existing one.

Truncating the class or reference lanes to a minimal set fails with
`Corrupt data found when loading an OM file` (code 580044) even when the middle
and record lanes are preserved. The object lane references class ordinals, so a
minimal hand-authored schema must be paired with a re-encoded middle that uses
those ordinals.

The object/record lane of geometry parts is a run of seven-byte rows
`05, kind, token[2], code_a, code_b, 4e`. `variant400.prt` section 4 has four
rows, matching its fifth count word; section 2 has one row. `empty.prt` has no
rows.

Truncating the feature-history middle to its product record fails with
`An invalid class index was found reading an OM file: probable corruption`
(code 580114). The middle therefore carries class-ordinal references that must
match the class lane exactly; it cannot be replaced by a minimal product record.

Product-text edits work only at constant length. Replacing the feature-history
product text with a four-byte longer string fails with `Internal error:
Non-specific OM error` (580504); shifting the visible control words by the same
delta changes the failure to `The end of an OM file was reached unexpectedly`
(580066). The record lane has additional length and offset fields that must be
recomputed together.

Removing any one of the four sections from `empty.prt` and rebuilding the index
fails in NX 2506: without section 0 `580014`, without section 1 a memory access
violation (`11`), without section 2 `641001`, without section 3 `580027`. All
four sections and their full class tables are required even for an empty part.

A research spec pipeline (`re/nx/tools/FromSpec.py` over `SchemaEmpty.py`)
builds a complete part from constants plus a neutral spec: part name and product
text. Changing the saved part name requires updating the section headers, the
two middle-lane occurrences (`saved as "C:\<name>"` and the name frame), and
the `EXTREFSTREAM` self reference. With those updated, the generated part loads
in NX 2506 (`from_spec_named.prt`, `unloaded 0`). The schema and middle constants
are still captured from `empty.prt`, so this pipeline is research only and not
shippable under the donor rule.

Changing only the saved part name in the section headers fails with
`Corrupt data found when loading an OM file` (code 580044), so the name is
cross-referenced from another record lane. The middle and record areas are still
opaque and must be decoded before a section can be authored from neutral data.

### Empty-part schema is version-global

Two parts created independently by NX 2506 (`empty.prt` and `empty_alpha.prt`)
have byte-identical reference lanes, class lanes, and counts in all four
sections. That includes class names, storage and base tokens, and the eight-byte
schema fingerprints. The only differences are the flag high byte, the timestamp,
a ten-byte identity value inside the middle lane, the 12-byte section digest, and
the fields that carry the part-name length.

The class fingerprint is therefore a per-version schema constant and not a
per-document value. It is stable for the same class name across `empty.prt`,
`block.prt`, and `variant400.prt` (139 shared names, zero mismatches). It does
not match md5, sha1, sha256, xxh32, fnv64, or crc64 of the class name, so it is
assigned rather than derived.

The document GUID in the header trailer is free. Replacing it with a new random
version-4 UUID still loads (`new_guid.prt`, `unloaded 0`).

### Name length is an offset lane

The header name is a length-prefixed string. Growing it shifts every
body-absolute offset in the middle lane, and grows section 0 a second time
because section 0 also carries a file-name frame that stores `len + 2`. The
measured offset lanes are 216 fields in section 0, four in section 1, seven in
section 2, and three in section 3. Fields after the section-0 frame move by
twice the delta, and the section pointer moves the same way.

The payload index also stores offsets in all three words of a row, and its last
row points at `payload_length - 2`; every one of those must be remapped when any
section size changes.

`re/nx/tools/AuthorName.py` applies those rules to the researched empty-part
model. Generated parts with new names and new UUIDs load in NX 2506 and report
the expected part name with zero bodies, features, and expressions:

```text
RESULT ...\study_1.prt unloaded 0
  NAME study_1
  BODIES 0
  FEATURES 0
  EXPRESSIONS 0
RESULT ...\study_2.prt unloaded 0
  NAME study_2
  BODIES 0
  FEATURES 0
  EXPRESSIONS 0
```

### The feature-history middle is generated, not copied

The middle lane of the feature-history section is now produced from structure
rather than sliced from a document (`re/nx/tools/MiddleGen.py`):

- eight flag bytes that carry class tokens and lane counts
- four little-endian control words (`2`, `1`, `3`)
- three computed body offsets: the text record, the `41` system anchor, and the
  first `05 <token> 00 00 <token> <token>` state record
- the product text record `03 01 <len+2> <text> 00`
- the `08 SYSTEM 00` anchor and the state lane

Re-encoding reproduces the captured middle byte for byte on all five NX 2506
saves that have the lane:

```text
empty.prt       section 3 roundtrip True  176 176
block.prt       section 3 roundtrip True  888 888
block50.prt     section 3 roundtrip True  888 888
variant400.prt  section 3 roundtrip True  903 903
variant40000.prt section 3 roundtrip True  903 903
```

Because the offsets are computed, the product text can change length. A block
part rebuilt with a four-byte longer product text in that lane loads in NX 2506
with full parity:

```text
STATUS 0
BODIES 1
FEATURES 2  DATUM_CSYS, BLOCK
EXPRESSIONS 6
VOLUME 23999.999999999996
AREA 5200.0
MASS 0.18793536
```

The payload index also names four reference points for each section, not one:
`offset`, `offset + 12`, `offset + 12 + size`, and `offset + 12 + size + 4`.
Leaving any of them stale makes NX report `Part file is corrupt` (641001) even
though the section bodies are consistent.

### Class and reference lanes come from a table

`re/nx/tools/SchemaTable.py` names every declaration as data: reference name and
code, and class name with its storage code, base code, eight-byte fingerprint,
and reference code. `SchemaBuild.py` emits the two lanes by concatenation, and
the result is byte-identical to the captured lanes in all four sections:

```text
sec 0 refs 1468 1468 True classes 4795 4795 True
sec 1 refs  164  164 True classes  592  592 True
sec 2 refs   64   64 True classes  464  464 True
sec 3 refs   25   25 True classes  306  306 True
```

An empty part assembled from that table, with a fresh UUID and a generated
feature-history middle, loads in NX 2506:

```text
RESULT ...\schema_built.prt unloaded 0
  NAME schema_built
  BODIES 0
  FEATURES 0
  EXPRESSIONS 0
```

### Middle lanes round-trip, but only one tolerates text growth

With the offset lane learned from two saves that differ only in name length,
every middle reproduces byte for byte:

```text
empty.prt        sections 1 2 3 roundtrip True
block.prt        sections 0 1 2 3 4 roundtrip True
variant400.prt   sections 1 2 3 4 roundtrip True
```

Changing the product text length is safe only in the feature-history section. In
a part with geometry, growing the text in other sections fails even though every
learned offset is updated:

```text
sections {3}    payload 68039  loads
sections {1,3}  580504  non-specific OM error
sections {2,3}  580044  corrupt OM data
sections {0,3}  580028  O/S file i/o operation failed
sections {4,3}  580504  non-specific OM error
```

So those sections carry additional length or offset fields that the name-delta
lane does not include. They still need a structural decode.

### One expression costs 155 bytes in section 2

NX 2506 saved two parts that differ only by a single expression
(`kit_len = 12.5`). The parts differ as follows:

- section 2 gains three classes: `UGS::EXP_expression`,
  `UGS::EXP_generic`, and `UGS::ModlUtils::CachedWaveLinkData`
- section 2 gains one reference, `UGS::ModlUtils::CachedWaveLinkData`
- the section counts change from `(6, 1, 0, 14, ...)` to `(7, 1, 0, 17, ...)`
- the section 2 middle grows from 337 to 492 bytes

The record itself ends with:

```text
02 02 04 09 kit_len 00 04 06 12.5 00 ff 00 0a 00 ... 82 c0 01 00 50 49 00 00 00 00 ff
```

so the expression name and its formula each use `04 <len+2> text 00` framing.

Editing the name field works: a rebuilt part reports `kit_abc` in NX 2506.
Editing the formula string alone does not change the reported value.

The value is the 16-bit field after the `82 c0 01 00` marker at the end of the
record. Editing that field changes what NX reports:

```text
0x4950 -> 12.5       (source value)
0x5950 -> 25.0
0x2850 -> 3.0
```

A 40-value sweep (`0.25` to `10.0` in `0.25` steps, one part) shows the field is
not a numeric encoding. It is a per-part handle: the same value receives a
different handle in a different part.

```text
value    sweep.prt   multi.prt
0.5      0x0850      0x0003
1.0      0x1450      0x0001
2.0      0x2250      0x0002
3.0      0x2a50      0x2850
```

Within one part the handles are allocated in creation order, with small integers
for the first few values and a larger form afterwards. Editing the handle in an
existing part changes what NX reports only because the new handle already
resolves to another value in that part's own table. That is why an earlier edit
appeared to prove a numeric encoding.

The value table is visible in the first record of the same middle lane:

```text
01 05 03 "1" 00 03 "2" 00 03 "3" 00 05 "0.5" 00
```

So an authored expression needs a new handle plus a matching table entry, not a
16-bit number.

The handle is a 16-bit float: a four-bit exponent in the high nibble and a
mantissa in the low twelve bits.

```text
handle = (E << 12) | (0x50 + round((value / 2^(E-1) - 1) * 4096))
E      = floor(log2(value)) + 1
```

`0x50` is a fixed tag, not data. Values 1 and 2 use the compact form where the
handle equals the value. The formula reproduces every captured handle:

```text
   0.75  known 0x0850 encoded 0x0850
   3.00  known 0x2850 encoded 0x2850
   3.25  known 0x2a50 encoded 0x2a50
   7.75  known 0x3f50 encoded 0x3f50
  10.00  known 0x4450 encoded 0x4450
  12.50  known 0x4950 encoded 0x4950
  13.50  known 0x4b50 encoded 0x4b50
  25.00  known 0x5950 encoded 0x5950
 100.00  known 0x7950 encoded 0x7950
```

Computed handles were then written into a real part and NX reported the authored
numbers:

```text
handle 0x3250 -> EXPRESSION kit_len 4.5
handle 0x6450 -> EXPRESSION kit_len 40.0
```

An unknown handle is not tolerated: `0x1234` makes NX report `The end of an OM
file was reached unexpectedly` (580066). Values below `0.75` use a compact form
that is not yet derived, so the encoder refuses them.

No value appears anywhere in the container as a binary64, a shifted binary64, a
float32, or UTF-16 text.

### Offset list and count words decoded

The per-object offset list is `6 + n` entries and every entry is a landmark in
the emitted layout. Predicting them from landmarks matches the captured lists on
all four saves:

```text
empty.prt      6 entries  equal True
empty_expr.prt 7 entries  equal True
multi.prt      14 entries equal True
sweep.prt      46 entries equal True
```

The landmark order is:

```text
anchor, anchor + 0x1b, names - 1, trailer, trailer + 4, last default record - 2,
then one entry per object record
```

The count words are `7 + n` values. The first value is `6 + n`, followed by
`1, 3, 5, 4, 6, 7`, and then one value per object:

```text
n = 0   6 1 3 5 4 6 7
n = 1   7 1 3 5 4 6 7 8
n = 8   14 1 3 5 4 6 7 14 15 8 9 10 11 12 13
```

### NX never rebuilds geometry on open

Feature parameters and body geometry are independent in a saved part. NX reads
the stored body and reports its measurements; it does not replay the feature
history to recompute them.

Three independent saves prove this:

```text
dim60_delayed.prt  NX save with ModelUpdateDelay, p0=60
                   open -> EXPRESSION p0 60.0, VOLUME 23999.999999999996
                   DoUpdate -> VOLUME 23999.999999999996

pend60.prt         NX save: suppress, update, delay, unsuppress, p0=60
                   open -> BODIES 1, p0 60.0, VOLUME 23999.999999999996

dim4_all.prt       our own patch of expression, dimension handle and
                   dimension text -> p0 60.0, VOLUME 23999.999999999996
```

So a dimension edit without a matching body write produces an inconsistent but
loadable part, and NX will not repair it. Authored geometry means authored body
data, not authored parameters.

### The geometry stream is a re-writable zlib partition

Each body is one stream in the object-model payload:

```text
offset 42193, compressed 3414, inflated 6722 for dim40.prt
45 byte header, then zlib data
header +0x04  compressed size
header +0x0E  compressed size again
inflated      PS\0\0\0 3: TRANSMIT FILE created by modeller version 3701250
```

`re/nx/tools/GeoSwap.py` replaces that stream, patches the two size fields and
the payload rows, and reseals the container. Recompressing the identical
inflated bytes loads (`geo_same.prt`, `unloaded 0`), which proves the framing and
the splice are correct.

Kit's own Parasolid encoder is accepted by NX when it writes the model form:

```text
EncodeBrepModel(Model, PartValue=False)
  PS\0\0\0 3: TRANSMIT FILE created by modeller version 1200000
  ... SCH_1200000_12006 ...

geo_model.prt  decoded NX box re-encoded and spliced
  unloaded 0, BODIES 1, FEATURES 1, EXPRESSIONS 3
  VOLUME 23999.999999999996, AREA 5200, MASS 0.18793536
```

### An authored box loads but is not measured as a solid

`re/nx/tools/GeoAuthor.py` builds a box from constants with
`BuildPrism("body", Transform(), four lines, 0, height)` and splices the encoded
model:

```text
authored_box60.prt  60 x 30 x 20 from BuildPrism
  unloaded 0, BODIES 1, FEATURES 1, EXPRESSIONS p0 60.0 / p1 30.0 / p2 20.0
  VOLUME 0.0, AREA 0.0, MASS 0.0
```

The encoded model itself is sound: it decodes back to one body, one closed solid
region, six faces with outward plane normals, twelve edges and eight vertices,
and it computes volume 36000 and area 7200 before encoding.

What is missing is the object-model contract: NX's stream carries extra
attribute records (`body_id`, `UGS/ObjectState`, density, group owners) that tie
the Parasolid body to the body object in section 0. A body without them is
listed by NX but not measured.

### Authored topology still needs the NX shell orientation

Four variants of the same authored box were measured in NX 2506 to isolate what
the object model needs beyond the encoded geometry:

```text
BuildPrism as built                       BODIES 1, VOLUME 0.0,     AREA 0.0
+ plane origins moved to face centroids   BODIES 1, VOLUME 0.0,     AREA 0.0
+ line origins at midpoints, edge params
  +-length/2                              BODIES 1, VOLUME 0.0,     AREA 0.0
+ parasolid order / fin attributes        BODIES 1, VOLUME 0.0,     AREA 0.0
+ loop traversal reversed                 BODIES 1, VOLUME 6000.0,  AREA 600.0
+ plane normals flipped                   BODIES 1, VOLUME 0.0,     AREA 0.0
+ loop reversal and normal flip           BODIES 1, VOLUME 0.0,     AREA 0.0
+ loop reversal and same_sense flip       BODIES 1, VOLUME 0.0,     AREA 0.0
+ clockwise profile                        BODIES 1, VOLUME 0.0,     AREA 0.0
```

The reversed-loop model itself is exact: it decodes back with signed volume
`-36000.0`, the same sign as NX's own box, so the topology is a closed inverted
shell. NX still measures `6000` for it, which means the orientation sign alone
does not satisfy the reader.

So `body_id`, density and the `UGS/ObjectState` records are not the blocker: the
encoder already writes density, timestamp, matching and atom identifiers, and
adding the ordering and fin attributes changes nothing. What changes the result
is loop traversal, and the reversed variant measures a wrong shape rather than
the authored one, so the flip is not the correct convention either.

A direct measurement shows the mismatch. Integrating the divergence over the
decoded loops gives:

```text
NX box 40 x 30 x 20        signed volume -24000.0
BuildPrism box 60 x 30 x 20 signed volume +36000.0
```

NX stores box shells with the opposite loop orientation to the one
`BuildPrism` produces, and NX only measures a body whose shell follows its own
convention. Reproducing that convention for an authored topology is the
remaining piece for a body written entirely from constants.

### Identity, ordering and convention are now all ruled out by direct test

Four more oracle runs pinned down what is left. All of them use the same
40 x 30 x 20 box that NX itself saved, so geometry values are identical between
the working and authored streams.

```text
authored faces/surfaces numbered in creation order           VOLUME 0.0
authored faces numbered from the source body's ids           VOLUME 0.0
decoded body with its face list reversed                     VOLUME 24000.0
decoded body with its surface list reversed                  VOLUME 24000.0
decoded body with its vertex list reversed                   encoder refuses: changes vertex geometry
```

So numeric attribute identity is not the contract, and neither is list order:
the encoder reproduces the same body when whole record lists are permuted.
Permuting vertices is refused by `VerifyBrepData`, which proves the rank
attributes are positional and consistent.

The strongest variant aligned everything the model exposes: entity ids mapped by
geometry key, record lists sorted into the source body's order, `parasolid.*`
ranks re-derived from that order, `first_fin` and `vertex_fins` rebuilt, surface
origins, normals and reference directions copied from the matching source
surface, curve origins and directions copied, and edge parameters copied.

```text
aligned authored body vs decoded body   3393 bytes each, 586 differing bytes
                                        VOLUME 0.0
```

### Every section anchors its saved state on one identity

Sections 1, 2, 3 and 4 each store a seven byte identity immediately after the
three byte marker `e0 6a f8`, and the identity can be the unset constant in place:

```text
const_box60 section 2 identity replaced with ff x 7, nothing else touched
  STATUS 0  BODIES 1  EXPRESSIONS 3  p0 40.0  p1 30.0  p2 20.0
  VOLUME 36000.0  AREA 7199.999999999999  MASS 0.28190304
```

Same experiment with other values, on the construction section:

```text
ffffffffffffff  loads
01010101010101  refused
00000000000000  refused
```

So `ff` is the portable placeholder and the writer now patches this field in
sections 1 (block shape), 2 and 3, in addition to regenerating section 3 and
emptying section 4. Section 0 keeps its source anchor because its body is still
copied.

### Generated middles need the document counter from the source

Two constants were wrong until a part with a different counter was written. The
counter is a per document high water mark, not a format constant:

```text
section 1 counter     empty 0x3d8   multi 0x3d8   var_blank 0x3dc   dim40 0x3d8
section 3 counter     empty 0x1e3   multi 0x1e3   var_blank 0x1e7   dim40 0x1e3
```

`ConstructMiddle` emits it at middle offset `0x2c` and derives two later values from
it; `RootMiddle` emits it at offset `0x08` and derives offsets `0x2c` and `0x30`. With
the counter read from the section being replaced, both generators reproduce all five
fixtures byte for byte, and `var_blank.prt` stops being the only part that NX refuses.

### The head tail integers are not validated

The two variable length integers at the end of the head record are not validated
field by field. Each byte of them was mutated in `const_box60.prt` and loaded:

```text
first integer byte 0    loads  bodies 1  exprs 3     second integer byte 0  loads
first integer byte 1    loads  bodies 1  exprs 3     third integer byte 0   loads
the 0x13 after them     loads  bodies 1  exprs 3     last two bytes         loads
```

So the encoding does not have to be understood to change those bytes.

They are not, however, interchangeable as a whole. Replacing the full head with the
canonical body-less tail and a fitted text loads for `empty.prt`, `multi.prt`,
`var_blank.prt` and `dim40.prt`, but not for `const_box60.prt`, which is the part
whose geometry was authored by Kit:

```text
empty / multi / var_blank   generated head, tail 80 d5 02 ...  loads
dim40                       generated head, tail 80 d5 02 ...  loads
const_box60                 generated head, tail 80 d5 02 ...  OPEN_FAILED
const_box60                 source tail, other text            OPEN_FAILED
const_box60                 head text patched in place only    loads
```

Changing the record length is also refused for every part with a body
(`74 -> 93`, `74 -> 43`, `74 -> 81` all fail while `74 -> 74` loads). So the emitter
is enabled only when the source head already carries the canonical body-less tail and
the generated record keeps that length; every other shape keeps its source record.

### Section 0 field grammar

Single field mutations in `empty.prt`, each loaded in NX 2506:

```text
head tag 41 -> 42                  refuses     head anchor changed       loads
head kind 03 03 -> 03 04           refuses     head identity -> ff x 7   loads
head length prefix 22 -> 21 or 23  refuses     head path text changed    loads
record 4 any byte                  loads       record 1 or 2 tail zeroed refuses
record 3 or 6 id byte              loads       class id in header        refuses
```

So tags, length prefixes and index lists are validated while text, anchors,
identities, instance ids and trailing words are free. Changing the head text also
requires the section pointer to shift, because that field names the end of the
middle: the record table stays consistent but the pointer is absolute.

The head tail ends with two variable length integers that depend on the document
(`80 d5 02` for a body less part, `fa 02` for one with a body), so the emitted
record is only accepted when its length matches the source shape.

### All 214 section 0 records were mutated; five are optional

Each of the 214 records in `empty.prt`'s section 0 was blanked to `0xff` in place,
keeping the length and the table, and every part was loaded in NX 2506
(`mut_NNN.prt`, batches through `InspectDir.py`):

```text
records 0..213 tested
survivors   112  113  114  115  116      each loads: STATUS 0, UNITS 1, BODIES 0
the other 209 records are required; blanking any one makes NX refuse the part
```

The five survivors are one byte records:

```text
rec 112  0x36      rec 114  0x28      rec 116  0x1a
rec 113  0x2d      rec 115  0x22
```

so they are scalar values rather than structures, and invalid ones are tolerated.
That is the whole extent of what section 0 will accept: 209 of 214 records must be
correct, which is 97.7 percent of the graph.

### The instance-id family is checked across records, not within one

The `02 02 41 4d` family (14 records, 27 / 34 / 48 bytes) has a fixed 21 byte frame
`02 02 <class> 4d 00 f0 05 02 03 01 03 01 c0 45 04 00 80 86 02 00 01`, then a tail of
tagged values and zero padding, ending `01 00`:

```text
27 bytes  tail 00 00 00 00 01 00
34 bytes  tail 00 00 30 a4 a0 17 42 b2 81 da 00 01 00
34 bytes  tail 30 a5 00 f7 77 4c 1f c5 00 00 00 01 00
48 bytes  tail 30 9f 89 af bb 0b 42 a7  b0 99 aa b3 11 01 0c 47  30 90 78 58 61 56 b4 b8  00 01 00
48 bytes  tail 30 98 13 b6 4b b3 5b 12  b0 98 13 b6 4b b3 5b 12  30 98 13 b6 4b b3 5b 12  00 01 00
```

Mutating one record fails, but relabelling a value everywhere succeeds:

```text
one value byte changed                        loads
the value run replaced inside one record      OPEN_FAILED
every occurrence of a5 00 f7 77 4c 1f c5
  replaced by 11 22 33 44 55 66 77 (8 places)  loads
every occurrence of a4 a0 17 42 b2 81 da
  replaced by 88 99 aa bb cc dd ee (4 places)  loads
```

So the previous reading, that the group is validated as an aggregate, was wrong. The
values are shared references: replacing them in one place leaves stale duplicates
elsewhere. Replaced consistently, NX accepts any value, which is the same conclusion
the pair family gave.

What blocks full emission is the padding rule. Tail length is 6, 13 and 27 bytes for
zero, one and three values, which is 7 bytes per value over a 6 byte base, but the zero
padding moves between the front and the back of the value list across records, so the
boundary cannot be placed for every shape.

The padding is a rule after all, once it is read as padding rather than as part of the
group: each value is preceded by a tag byte, the padding zeros sit before the first tag
and after the last value, and the tail always ends `00 01 00`. So the value runs are
found by skipping zeros to the next `30` or `b0` tag and taking the seven bytes after
it, which gives zero runs for the 27 byte shape, one for the 34 byte shape and three
for the 48 byte shape:

```text
empty.prt   instance records 16   value runs 12   distinct values 6
```

`RelabelRefs` now uses that rule for every shape, and replaces each value at every
occurrence because the values are shared. Section 0 carries 260 generated bytes for a
body less part against 176 before, and all five fixtures still load.

### Views appear under two class tags and there is a value record family

The named views are not one family. Counting the head bytes:

```text
02 02 41 41   Front Right Back Bottom Left L1 L2 L3 L4 !DRAWING   10 records
02 02 41 4b   Front Back Bottom                                    3 records
```

the second group carries the same layout, `41 00 f0 03 46 00 a7 01 66 48 03 <len> <name> 00`,
then a matrix and extents, and its name is at the same relative place, so a view reader
has to accept both tags.

The 15 byte records are values rather than labels:

```text
50 34 00 00 02 30 66 80 00 00 00 00 00 03 00
```

`50 34` is `Encode(5.0)` in the expression handle encoding measured earlier
(`5.0 -> 0x3450`, little endian `50 34`), so this record carries a numeric value, a
tolerance and a flag. Emitting it means emitting the handle encoding, not relabelling.

### Thirty records share one lane grammar

The `02 11` to `08 11` records are one family with a count dependent flag run:

```text
<n> 11 <n> 01 11  <flags>  02 e0 <4 byte mask> 01 11  <tokens>
```

| n   | flags                                              | mask        |
| --- | -------------------------------------------------- | ----------- |
| 2   | 01 x 17                                            | 55 55 55 56 |
| 3   | 01 x 9, 02, 01 x 9                                 | 55 55 95 56 |
| 4   | 01 x 7, 02, 01 x 7, 03, 01                         | 65 55 95 56 |
| 5   | 01 x 5, 04, 01, 02, 01 x 6, 03, 01                 | 65 55 99 56 |
| 6   | 01 x 3, 04, 01, 02, 01 x 4, 05, 01, 03, 01         | 66 55 99 56 |
| 7   | 01, 06, 01, 04, 01, 02, 01 x 4, 05, 01, 03, 01     | 66 55 99 96 |
| 8   | 01, 06, 01, 04, 01, 02, 01, 07, 01, 05, 01, 03, 01 | 66 65 99 96 |

So the flag run is a depth first nesting of leaf markers and small counts, and the mask
packs the same shape into four bytes with one nibble per level. Tokens are `ff` empty,
`80 <label>` or `10..7f` occupied, and `03 <len> <text>` for labelled text such as
`03 07 20 54 48 52 55 00` (`" THRU"`).

All 30 records round-trip byte for byte, and relabelling every occupied token with one
global map keeps them shared. That adds 30 generated records to the writer:

```text
part           lane records  section 0 differing  payload identical
empty.prt                30                  340              99.00 percent
const_box60.prt          30                  214              99.46 percent
```

### The longest 02 02 41 00 records tolerate value rewrites

The 62 and 70 byte shapes carry fixed point words, and those are writable too:

```text
62 byte record, all three 50 79 00 00 words -> 50 7a 00 00   loads
62 byte record, only the first word changed                  loads
62 byte record, the eight 02 flags rewritten                 loads
70 byte record, both 2f c9 99 99 a0 00 00 00 words changed   loads
70 byte record, only the first word changed                  loads
```

So the whole family is value free; only its structure and length have to be reproduced.
The writer leaves the words alone because they carry model data rather than labels.

### The 02 02 41 00 family is label free as a whole

The family is twelve records in six shapes:

```text
10 bytes 02 02 41 00 36 58 c0 20 03 01
12 bytes 02 02 41 00 36 41 04 01 00 01 01 01
14 bytes 02 02 41 00 38 01 03 02 <6 bytes, one 81 marker among zeros>   x4
15 bytes 02 02 41 00 35 03 04 01 c0 45 04 00 4d 81 04
35 bytes 02 02 41 00 36 41 04 01 01 11 <token list>      (the slot record)
62 bytes 02 02 41 00 35 <id> c0 20 03 01 c0 41 04 00 80 85 81 04 <words> 80 85 ...
70 bytes the 62 byte shape with 80 d8 tokens and three fixed point words
```

Single byte mutations all load, so nothing in the family is a checksum over itself:

```text
81 marker in a 14 byte record -> 82             loads
a 00 slot in a 14 byte record -> 01             loads
trailing flag of a 14 byte record flipped       loads
10 byte record last byte changed                loads
12 byte record bytes 10 and 11 changed          loads
62 byte record 80 85 -> 80 86 at both spots     loads
62 byte record 80 85 -> 80 86 at the first spot loads
70 byte record 80 d8 -> 80 d9 at both spots     loads
15 byte record 4d -> 4e                         loads
```

Relabelling every distinct `80 <x>` token in the family to a counter from `0x10`, and
rewriting all 21 occurrences consistently, loads on all five fixtures. So the family
behaves like the pair and instance families: the values are references and the writer
may assign them.

````
### The decoded families are now generated, not copied

`ObjectSection.RewriteRecords` re-emits every attribute and pair record with labels the
writer assigns, and `nx.author_sections` runs it on section 0. Section 0 stops being a
byte for byte copy:

```text
part             rewritten   section 0 differing bytes   payload identical
empty.prt               88                       102        99.66 percent
multi.prt               88                       102
var_blank.prt           88                       102
const_box60.prt         88                       102        99.73 percent
dim40.prt               88                       102
````

All five still load in NX 2506, so the labels really are free at load time. The number
is small against 36694 bytes of section 0, because only two of the sixteen families are
decoded so far.

### Ids and ordinals in the decoded families are labels

Rewriting the values across a whole family, rather than one record, decides whether
NX treats them as data or as labels:

```text
15 pair records with the two ids swapped            loads
14 pair records with both ids raised by one         loads
77 attribute ordinals raised by one                 loads
77 attribute ordinals all set to 0x40               loads
8 records of the 02 02 41 4d family filled with 11  OPEN_FAILED
```

So the pair ids and attribute ordinals are free: NX rebuilds whatever index it needs
on load, and an emitter may assign its own values. The `02 02 41 4d` family is not
free that way, which means its id region contains a length prefix or sentinel rather
than a plain value.

The earlier conclusion that section 0's ids must stay mutually consistent was too
strong: whole-group nulling failed because it collided with sentinels, not because
the values were being checked.

### Two record families are decoded

The attribute family (`01 02 04`, 77 records) is a key and value pair with an
ordinal and a one byte marker:

```text
01 02 04 <len(key)+2>  key 00   01 02 04 <len(value)+2>  value 00   <ordinal> <marker>
```

Examples, which also show that the marker is `01` for some records and `00` for
others:

```text
01 02 04 03 58 00 01 02 04 02 00 2f 01          key X   value ""     2f 01
01 02 04 03 2d 00 01 02 04 07 20 44 45 45 50 00 31 01   key -   value " DEEP"  31 01
01 02 04 0c 4d 61 6a 6f 72 3a 3c 6f 3e 20 00 01 02 04 02 00 10 00   key Major:<o>  10 00
```

The pair family (`03 11`, 15 records) is a 30 byte frame, a registry token, six
absent slots, another token and eight absent slots:

```text
03 11 03 01 11 01 x 7 02 01 x 9 02 e0 55 55 95 56 01 11  <token> ff x 6 <token> ff x 8
```

Both families round-trip byte for byte across all three body-less fixtures, which is
92 of 214 records. The ids and ordinals inside them still come from the source, so
the grammars make the records re-emittable rather than derivable.

### Section 0 is a record dictionary of 116 shapes

Counting each record by length and first four bytes, the three body-less parts are
identical:

```text
part            records  distinct shapes
empty.prt           214              116
multi.prt           214              116
var_blank.prt       214              116
```

The most common shapes are:

```text
size 21  head 01 02 04 0b   x18        size 27  head 02 02 41 4d  x5
size 13  head 01 02 04 03   x13        size 34  head 02 02 41 4d  x5
size 20  head 01 02 04 05    x8        size 14  head 02 02 41 00  x4
size 46  head 03 11 03 01    x8        size 62  head 02 02 41 00  x3
size 12  head 01 02 04 02    x7        size 46  head 05 11 05 01  x3
size 48  head 03 11 03 01    x6
```

So the dictionary is a small number of record families with names and ids inside,
not 214 unrelated blobs.

### Group nulling does not remove the id coupling

Two groups were regenerated across the whole dictionary rather than one record:

```text
trailing 00 01 00 zeroed in 18 records                    loads
12 byte id region after 02 02 ?? 4d zeroed in 14 records  OPEN_FAILED
same region replaced with a position derived sequence     OPEN_FAILED
```

The trailing words are free; the id regions are not, because records reference each
other through them. A single id byte can change and the part still loads, but the
whole group has to stay mutually consistent, so emitting section 0 needs an id
allocator over the dictionary rather than replacement of individual fields.

### Every section 0 record is load bearing

Controlled mutation of one record at a time in `empty.prt`'s section 0, keeping the
length and the table unchanged, then loading in NX 2506:

```text
records 0..79 and 100..109 replaced with 0xff   every part OPEN_FAILED
records 0..29 replaced with 0x00                every part OPEN_FAILED
records 4, 20, 100 kept and the rest dropped    every part OPEN_FAILED
```

So no record can be blanked, and the graph cannot be truncated. Section 0 has to be
emitted in full: 214 records, 24495 bytes, plus the 129 class entries.

Mutating a class identifier in the header also fails:

```text
cls_mut1.prt   first class id byte 0x64 -> 0x74   OPEN_FAILED
cls_zero.prt   first class id zeroed              OPEN_FAILED
```

which means the identifiers are validated against the records that reference them,
so they cannot be invented either.

### The class table is scoped to the class set, not the document

Twelve parts were compared entry by entry:

```text
group      parts  same class set  same entries
body-less      5            True          True
block          8            True          True
```

The block group is `dim40`, `dim50`, `dim60`, `const_box60`, `var_two`, `var_named`,
`var_formula` and `var_datum`. They differ in dimension, in expression count (three to
six), in expression names, in body count (one or two) and in feature count, and their
class tables are identical in every byte. `var_datum.prt` was created for this test as a
block plus a fixed datum plane through `CreateFixedDatumPlane(point, matrix)`, and its
section 0 is 28995 bytes against `dim40`'s 28986, with the same 154 classes.

The reference hypothesis is refuted: `dim40` and `var_sph` carry the same 79 references
in the same order and still differ in 152 of 153 entries. `var_sph.prt` is the block set minus one class, `UGS::Solid::Edge`, and 152
of its 153 entries differ. `var_cyl.prt` has 161 classes and differs too.

Decoded as little-endian 7-bit fields, an entry is a short sequence of small integers
and only one changes between sets:

```text
part          classes  refs  UGS::OM::RootObject fields
empty.prt         129    63  56, 100, 9648, 56917797, 15606, 2
dim40.prt         154    79  56, 116, 9648, 56917797, 15606, 2
var_sph.prt       153    79  56, 115, 9648, 56917797, 15606, 2
var_cyl.prt       161    83  56, 120, 9648, 56917797, 15606, 2
```

The increment is 0, 16, 15 and 20; it is not the class count difference (0, 25, 24, 32)
and not the reference difference alone, since `var_sph` and `dim40` share 79 references
but differ by one. In each class's entry the increment lands at a bit offset that varies
by class, which is why raw entries differ in different byte positions and why a plain
integer offset never matched.

So the table is a per class set constant, not per document data. That makes it cacheable
and means a rewrite never has to touch it, but the class constants and the offset rule
are still not derived.

### The class identifier delta is not an offset

Testing whether the per-document change is a counter applied to a fixed base per class
name, by decoding the entries as big-endian integers and looking for a constant
difference:

```text
128 of 129 shared classes differ between empty.prt and dim40.prt
no constant offset explains them, searched up to 4096
line length pairs   11->11 x12   12->12 x56   12->13 x35   11->12 x4   13->13 x13   13->14 x8
differing positions  byte 1 x12  byte 2 x56  byte 3 x13  byte 10 x8  byte 11 x50  byte 12 x13
delta magnitudes     16 x49     18 x15     13 x2     4 x40      5 x10      6 x4
```

So the entry is a variable length encoding that changes in two separate digit
positions, one near the start and one near the end, and grows a byte for 47 of the 129
classes. That is the signature of two packed fields, not of a base plus a document
offset, and one of the fields moves with the document rather than the class.

The three body-less parts are identical in every entry, so the field moves with the
document's class population, not with the file name or path. Reproducing it requires
knowing what those two fields are, which the file corpus does not expose: no hash of
the class name I tried matches, and the deltas are not a constant.

### Section 0 class identifiers are per document values

The class table is identical across body-less parts, but not across a body part:

```text
empty vs multi vs var_blank   129 classes, map equal True
refs equal                    True
empty classes subset of dim40 False   128 of 129 differ
```

The differences are small and systematic:

```text
UGS::OM::RootObject    body-less 38 64 b0 4b a5 fe 91 1b f6 79 02
                        body     38 74 b0 4b a5 fe 91 1b f6 79 02
UGS::RM_part           body-less 65 67 8f c0 f7 e4 25 5a 70 c8 01
                        body     65 77 8f c0 f7 e4 25 5a 70 c8 01
UGS::POINT             body-less 83 84 69 0e 7e 9c 17 4a b9 d4 b5 05
                        body     83 84 80 80 0e 7e 9c 17 4a b9 d4 b5 09
```

One byte steps by `0x10`, and the last byte steps by a small amount, while the middle
bytes are unchanged. So the entry is an encoded value carrying a per document
component, not a fixed kernel identifier and not a hash of the class name.

That rules out shipping the class table as a name to identifier constant: the
identifiers have to be computed, and the function that computes them is in the
kernel. Reference entries are different: `UGS::OM::Meta` is `02` in every part and
the whole reference map is identical across body-less parts and a subset of the
body part, so references look stable.

### Section 0's body is fully mapped and cannot be reduced

The body-less section 0 recomposes byte for byte from five named regions:

```text
0x0000  780 bytes   names lane (7 member names) plus the flag lane
0x030c  856 bytes   object table, 214 body relative offsets
0x0664  852 bytes   order array, u32 count 212 then 212 indices
0x09b8   49 bytes   version block, SYSTEM then the modeller string
0x09e9 24495 bytes  214 object records
total 27032 bytes, recomposed identical True
```

The 214 records start with the head object that carries the part path
(`41 00 03 03 22 "Part renamed from "C:\empty.prt"" 00 ...`) and run to 62 byte
tails. Sizes range from 12 to 75 bytes.

Truncating the graph is refused. Keeping the first 4, 20 or 100 records, with the
table, order array and count updated to match, produces parts NX will not open:

```text
s0_keep4.prt    OPEN_FAILED
s0_keep20.prt   OPEN_FAILED
s0_keep100.prt  OPEN_FAILED
```

The header is 6351 bytes and carries 129 classes and 63 references. A class entry
is the class name plus an 11 or 12 byte big-endian value around 10^21, which is not
md5, sha1, sha256 or crc32 of the name, while a reference entry is a small varint
(`UGS::OM::Meta` is 2, `UGS::UGFONT` is 4). So class identity is a kernel assigned
identifier, not a name hash, and it is not reproducible from the class name.

That is the precise remaining blocker for a payload free writer: 24495 bytes of
object records and 129 kernel class identifiers, with no reduction accepted by NX.

### Section 0 is document independent for a part without a body

A third body-less part was created (`CreateBlank.py`, saved as `var_blank.prt`) and
its section 0 compared with `empty.prt` and `multi.prt`:

```text
part                  section 0  classes  refs
empty.prt   27032   129      63
multi.prt   27032   129      63
var_blank   27040   129      63
dim40       28986   154      79   (one body)
```

`empty` and `multi` have identical path lengths, and their section 0 middles differ
in exactly fifteen bytes, in three places:

```text
0xa04   named from "C:\empty.prt"      against "C:\multi.prt"
0xa1a   e0 6a f8 <7 byte identity>
0xd92   <len> "empty.prt"               against "multi.prt"
```

`var_blank` is eight bytes longer, exactly the difference between `C:\empty.prt`
and `C:\var_blank.prt`. So section 0 for a body-less part is a fixed class and
record schema whose only per document fields are the full path, the base name and
the anchor identity.

That matters because section 0 is the last section without a generator. It is
also 27032 bytes, so the generator has to emit the class dictionary and its records
rather than copy them: 129 class names account for only about 2.5 kB, and the
remaining 24 kB is record structure that has to be derived field by field. Shipping
the captured body would be a donor block, so it is not an option.

The growth with a body is `+1954` bytes and `+25` classes, which is the topology
class set, and that part stays model dependent.

### The expression section is a hash table that NX does not revalidate

Three fixtures were generated to vary the expression to attribute binding rather
than the feature type (`CreateExprVariant.py`): a block whose dimensions are
renamed to `length`, `width` and `height`, and a block whose `p1` is edited to the
formula `p0/2`.

Renaming the expressions in place, without touching anything else, is accepted:

```text
dim40 section 2, p0 p1 p2 replaced by aa bb cc (same lengths)
  STATUS 0  BODIES 1  EXPRESSIONS 3
  EXPRESSION cc 20.0   EXPRESSION bb 30.0   EXPRESSION aa 40.0
  VOLUME 23999.999999999996
```

So the section is a hash table keyed by expression name, but NX does not
revalidate the bucket layout on load. That is what makes emission possible: a
canonical layout with generated names is accepted.

Values are carried by a two byte handle, not by the text:

```text
Encode(40.0) = 0x6450 -> 50 64      Encode(30.0) = 0x5e50 -> 50 5e
Encode(20.0) = 0x5450 -> 50 54      Encode(12.5) = 0x4950 -> 50 49
```

Patching only the five `50 64` occurrences in `dim40`'s section 2 to `50 6e`
(`Encode(60.0)`) makes NX report `EXPRESSION p0 60.0` with the body unchanged.
Patching the `40` text instead makes NX refuse the file, so the text is a display
string that must stay consistent with the handle.

The record grammar is:

```text
02 02 04 <len(name)+2> <name> 00
  <len(text)+2> <text> 00        when the value is stored inline
  or 06 <slot> ff                when the value is shared with a slot object
  00 0a <10 bytes> 11 <index> 02 <count> 01 82 cc 01 <n> <handle> <handle> <handle> f0 00
```

and a slot object is `02 02 00 00 ff 00 00 21 01 01 01 01 01 00 <handle> 00 00 00 00 ff`
(21 bytes) or the same without the handle (18 bytes). Which expression is stored
inline and which is shared follows the hash order, which is why renaming moves the
`50 64` / `50 5e` / `50 54` handles between slots.

### The expression section inventory follows the feature, not the count

Six parts, measured object by object (`re/nx/tools/CmDump.py` locates the table by
its declared count):

```text
part            exprs  objects  18 byte  21 byte  slots  records
empty.prt           0        6        0        0      0        0
empty_expr.prt      1        7        0        0      0        1
var_sph.prt         1       10        3        1      4        1
var_cyl.prt         2       14        6        1      7        2
dim40.prt           3       24       10        5     15        3
var_two.prt         6       42       19       11     30        6
```

Two rules hold exactly:

- there is one record per expression (0, 1, 1, 2, 3, 6)
- the per expression slot count depends on the feature: five per expression for a
  block (15 for 3, 30 for 6), four for one sphere expression, three and a half for
  two cylinder expressions

so the object count is not a function of the expression count. It is a function of
how many attribute bindings each expression has, which is feature semantics rather
than file layout. That is the same conclusion the construction section gave, and it
is why the expression section cannot be emitted from `(name, value)` pairs alone.

The fixed part of the section is still worth emitting: head, lane descriptor, the
four `EXP_*` system names, the default group record, the occupancy lane and the
per expression record bodies are all schema constants, and `MiddleBuild` already
reproduces the body less middle (337 bytes) exactly.

### The expression section keeps a model dependent object graph

Section 2 carries a per document graph that grows with the expression count:

```text
part         expressions  objects  middle bytes
empty.prt            0         6           337
empty_expr.prt       1         7           492
dim40 / const       3        24          1043
```

The layout is the same shape as the construction section: flags lane, a body
relative pointer to the version block, a u32 object table, an order array headed
by the object count, then the version and `SYSTEM` anchor, the four `EXP_*` names,
the occupancy lane, the default group record and one record per expression.

```text
dim40 table at 0x54  24 entries, first 0x440 (= middle start + 0x149)
dim40 order at 0xb4  count 24 then 24 indices
dim40 version at 0x118, first expression record at 0x38b
```

The first pointer field is `middle start + version block offset` in all three
fixtures, and the object table entries are `middle start + object offset`, so the
table is computable; what is not yet derived is the object inventory, since three
expressions produce 24 objects against 6 for none.

Trying to substitute a body less expression section into a part with a body
(`s2_min.prt`) makes NX refuse the part, so the substitution route is closed: the
expression section has to be generated for the document it belongs to.

### The block construction template does not depend on dimensions

A block made through a different creation path (`CreateDiagBlock.py`, two
diagonal points) gives a controlled comparison against the origin-and-lengths
block:

```text
dim40 vs dim50      sizes identical           5 bytes differ, all inside the head identity
dim40 vs var_diag   sizes 169 -> 170, 231 -> 237   99 bytes over five objects
```

So changing the block's length changes nothing in the construction section: the
dimension values live in section 0 and section 4, not here. Two sessions making
the same 40 x 30 x 20 block differ only in identity and in regenerated ids:

```text
object  0  head            7 bytes   identity
object 20  BLOCK_PARMS    64 bytes   ids and the diagonal form
object 22  descriptor      1 byte    object index
object 23  entry           2 bytes   object index
object 43  tail          231 -> 237  ids
```

That is the enabling fact for emission: the per-body block template is a fixed
layout of forty one objects, and the only per document values are the seven byte
identity plus internal object ids, which `src` already emits as arbitrary values
for sections 1 (body less) and 3.

### A canonical captured graph is not an emitter

An earlier revision of the writer shipped the single block construction middle as
two constants split around the anchor identity. It reproduced `dim40.prt` byte for
byte, and NX measured the part, but 1240 of its 1247 bytes were a saved document's
bytes. That is a donor block and it has been removed.

The replacement must be a field emitter, and the measurements above say what it
has to reproduce: `3 + 41` objects for one body, `3 + 2 * 41` for two, with the
per body chain, the group byte, the `BLOCK_PARMS` record and the nineteen compact
entries. Until that exists, a part with a body keeps its source construction
graph, and the only construction sections `src` emits are the three object
body-less shape.

### Per body and document level objects separate cleanly

Comparing `var_two` (two blocks, 85 objects) with `dim40` (one block, 44) splits
the construction graph. Byte equality only survives for the 112 byte record,
because the descriptors embed object ids, so the split comes from the size
multiset:

```text
dim40 sizes     27, 28, 14 x 6,  16 x 12, 169, 112, 24, 21, 3 x 19, 231
var_two sizes   26, 28, 14 x 12, 16 x 24, 169, 112, 169, 24, 24, 21, 21,
                3 x 34, 4 x 5, 480
```

Everything that doubles belongs to a body: the fourteen and sixteen byte
descriptors, the 169 byte parameter record, the 24 and the 21 byte records, and
the three byte entries. What stays single is the head, the 28 byte descriptor and
the 112 byte record, plus a 480 byte record that only appears with two bodies.

So the one body block layout is:

```text
document level   3 objects   27 head, 28 descriptor, 112 record
per body        41 objects   14 x 6, 16 x 12, 169 BLOCK_PARMS, 24, 21, 3 x 19, 231
```

and `3 + 41 = 44` matches `dim40`, `3 + 2 * 41 = 85` matches `var_two`.

The descriptors also reveal the per body marker. Every descriptor carries a group
byte between `f0 <object>` and `09 <weight>`:

```text
body one   02 02 3f 41 00 01 66 06 f0 00 09 0a 93 8c
body two   02 02 3f 41 00 01 5e 07 f0 06 0a 03 93 8c
```

`09` for the first body, `0a` for the second, and the same for the sixteen byte
form. The link byte re-chains within a body (`66 65 64 63 62 61` then
`5e 5d 5c 5b 5a 59`), so a body's objects are a self contained chain ending at
its own parameter record. The compact entries carry the group too: `ff 41 1c`
and `3f 41 1c` in `var_two` against `ff 41 2d` in `dim40`.

### The construction graph is feature typed, not topology typed

New fixtures were generated with NX journals (`CreateCylinder.py`,
`CreateSphere.py`, `CreateTwoBlocks.py`) so the construction section can be
compared across features:

```text
fixture      bodies  faces  edges  objects  structures  feature parameter record
var_sph          1      1      0        9         7     147 bytes  SPHERE_PARMS
var_cyl          1      3      2       18        15     158 bytes  CYLINDER_PARMS
dim40            1      6     12       44        38     169 bytes  BLOCK_PARMS
var_two          2     12     24       85        76     169 bytes  BLOCK_PARMS x 2
```

`var_two` is exactly `2 * 44 - 3`, so the graph is additive over bodies and the
body less base of three objects is shared: objects = 3 + per body count.

The per body count is a property of the feature, not of the face and edge counts:

```text
sphere     6 = 9 - 3
cylinder  15 = 18 - 3
block     41 = 44 - 3
```

A linear model over faces and edges does not fit (`k + a * faces + b * edges`
gives `a + b = 4.5` from the sphere and cylinder), and the parameter record grows
with the feature instead: 147, 158 and 169 bytes for sphere, cylinder and block.

So emitting the one body construction section requires one template per feature
type, and the block template is now the best characterised: 41 objects at sizes

```text
27, 28, 14 x 6, 16 x 12, 169, 112, 24, 21, 3 x 19, 231
```

The three byte entries are the per face and per edge references, which is why the
block has nineteen and the sphere and cylinder far fewer.

### The body less section 1 middle is emitted from fields

`re/nx/tools/CmBuild.py` builds the 356-byte middle from named fields: the names
lane, eight `02` and nine `01` flag bytes, the `0x3d8` counter, sixty four zero
bytes, the three object offsets computed from the object sizes, the four word
order array, the version string and `SYSTEM` anchor block, and the head object
with its anchor and seven byte pointer. Two parts reproduce byte for byte:

```text
empty.prt   base 0x34c  len 356  identical True
multi.prt   base 0x34c  len 356  identical True
```

The table is computed rather than copied. Object offsets follow from the preamble
length plus the sizes, and the entries are the middle start plus each offset:

```text
generated 356 byte middle   identity ffffffffffffff   table [1033, 1060, 1088]   counter 0x3d8
empty.prt                   identity 3b17ffdb906210   table [1033, 1060, 1088]   counter 0x3d8
```

Splicing that middle into `empty.prt` with the unset pointer loads in NX 2506:

```text
cm_empty.prt        unloaded 0  bodies 0
cm_empty_unset.prt  unloaded 0  bodies 0
cm_empty3.prt       unloaded 0  bodies 0   (fully generated section, unset pointer)
```

The descriptor and the record are now emitted too, so the whole 356 byte middle
comes from the generator:

```text
descriptor, body less    02 02 ff x 10 00 41 ff x 5 06 00 f0 00 01 01 01 00 00
                          every optional reference is 0xff, meaning absent
record, body less         112 bytes, identical in empty.prt and multi.prt except two count bytes
```

The descriptor differs from a one body part only at eight positions, and the
record differs at exactly two:

```text
record positions 0x20 and 0x43    07 and 08 for a body less part
                                  0a and 0b once a body is present
```

So the descriptor holds optional single byte references that are absent when the
part has no body, and the record is fixed infrastructure with two counts. A part
written with this generated section, using the unset pointer instead of the
source's, loads in NX 2506 with `unloaded 0`.

### Section 1's minimum object set is three objects

Locating the table by its declared count rather than by a fixed offset makes the
tool exact for both shapes, and shows how small the body-less section is:

```text
part       objects  counts[0]  first offsets        sizes
empty      3        3          1033, 1060, 1088     27, 28, 112
multi      3        3          1033, 1060, 1088     27, 28, 112
dim40      44       44         1850, 1877, 1905...  27, 28, 14, 14, 14, 14 ... 3, 3, 231
dim60      44       44         1850, 1876, 1904...  26, 28, 14, 14, 14, 14 ... 3, 3, 231
```

So a part with no body carries exactly three objects: the head, one 28 byte
descriptor and one 112 byte record. The 41 extra objects in a part with one body
are the construction graph, and the class list says which families appear:

```text
body-less classes   17: RootObject, CM_part, SaveAuditTrail, SaveAuditTrailEntry,
                    FEATURE_RECORD, OptIntValue, CM_STUB_PARMS,
                    NXParasolidVersioningService, TaggedObject, StorableObject,
                    MethodicObject, VersionedObject, SubObject, RM_entity,
                    OptAttValue, FEATURE_PARMS, NativeVersioningService
one body adds       13: FACE_REFERENCE, EDGE_REFERENCE, BREF, CM_LIST,
                    BLOCK_PARMS, CM_BREF_DATA, CM_NODE, CM_reference,
                    CM_object, RM_entity already present, PRIMITIVE_PARMS,
                    CM_GENERIC_NODE
```

The whole body-less middle is 356 bytes and lays out as:

```text
0x00  18 "m_legacyInactiveModules" 81 0c
0x1e  02 02 02 02 02 02 02 01 x 9      flag bytes
0x28  u32 0x3d8                        counter
0x2c  32 zero bytes
0x4c  ...
0x70  u32 x 3                         object table, body relative
0x7c  u32 x 4                         order array headed by the object count
0x8e  03 01 27 "NX 2506.9120 - External User Function" 00 08 "SYSTEM" 00
      41 00 03 05 01 00 04 05 02 00 e0 6a f8 <7 byte pointer> 10 05 02 13 06 02 00 00
      head object with its anchor
      descriptor and the 112 byte record that carries "DELETE" and a 0.02 double
```

Emission order follows the table: head, 28 byte descriptor, then the 112 byte
record. The counter at 0x28 is 0x3d8 for both body-less parts.

### Section 1 descriptor grammar

`re/nx/tools/CmDump.py` decodes the table and every record, and the three
fixtures agree on the object layout:

```text
object  0        head, 27 bytes (26 in dim60): 41 00 03 05 01 00 04 05 02 00
                e0 6a f8 <7 byte saved pointer> 1d 02 13 1e 02 00 00
objects 1..19   typed descriptors
object  20      169 bytes, carries "BLOCK"
object  21      112 bytes, carries "DELETE"
object  22      24 bytes
object  23      21 bytes
objects 24..42  3 byte entries
object  43      a 6 byte entry list
```

A typed descriptor is a fixed shape:

```text
02 02 <class> 41 00 01 <link> <ref> <ref> f0 <object> 09 <weight> 93 8a
02 02 <class> 41 00 01 <link> <ref>       f0 <object> 09 <weight> 93 8c
```

`f0` carries the object index, `09` carries a weight, and the last two bytes are
`93 8a` for the sixteen byte form and `93 8c` for the fourteen byte form. The link
byte descends `52 51 50 4f 4e 4d 4c 4b 4a 49 48 47 46 45 44 43 42 41` across the
descriptor run, so the records form a linked chain in table order.

```text
dim40 and dim50: identical offsets and one byte lengths
dim60:           object 0 is 26 bytes, every later offset one lower
```

What is still missing for emission is the mapping from each of the 30 class names
to the class byte and the reference topology each descriptor names, which is the
object schema rather than the byte layout.

### Section 1's pointer table indexes object records

The monotonic u32 run at middle offset `0xcd` is a per object offset table, not a
middle offset list. Every value is a body relative offset, and there is exactly
one entry per object:

```text
part      counts[0]  entries  table ends  last offset inside body
dim40        44        44      0x17d      True
dim50        44        44      0x17d      True
dim60        44        44      0x17d      True
```

The record sizes fall out of consecutive differences and are identical across all
three fixtures except for the first record:

```text
record 0            27 bytes (26 in dim60)
records 1..43       28, 14 x 6, 16 x 12, 169, 112, 24, 21, 3 x 19
```

Record 0 is the head that describes the structures: `41 00 03 05 01 00 04 05 02
00`, then `e0 6a f8`, then the seven byte saved pointer, then `1d 02 13 1e 02 00
00`. Records after it are small descriptors with a `02 02` tag, a class byte such
as `3f` or `41`, a flag byte `f0`, a descending link byte (`52 51 50 4f 4e 4d 4c
4b`), and the `93 8c` trailer:

```text
02 02 ff 41 00 01 52 07 f0 00 09 03 93 8c
02 02 3f 41 00 01 51 04 f0 01 09 1f 93 8c
02 02 3f 41 00 01 50 05 f0 02 09 1c 93 8c
```

Because the table stores body offsets, a record that is one byte shorter shifts
every later entry, which is exactly the -1 seen between dim40 and dim60, and the
same reason the two middles differ by one byte. That also disposes of the earlier
idea that one byte of model content changed: the difference is the size of record
0 and the resulting renumbering of the objects behind it.

Immediately after the table at `0x17d` sits a u32 array of 44 indices (`0x18,
0x01, 0x03, 0x0d, 0x0c, ...`), one per object, which is the order the objects are
written in.

### Section 1 carries model content, not constants

Three NX-saved boxes of the same feature with different lengths show what
section 1 depends on:

```text
part      section 0  section 1 middle  differences in section 1
dim40     36694      1247              baseline
dim50     36683      1247              5 bytes, all in the 7 byte anchor
dim60     36695      1246              608 bytes, every pointer table entry is 1 lower
```

So the block length does not appear in section 1, but one byte of its content
does change between 40 and 60, and that one byte shifts every record pointer in
its table by one. Section 1 therefore encodes an object graph that is a function
of the model, not a constant template.

Empty middles are refused, so the objects themselves are required and not only
their class tables:

```text
section 1 middle emptied, classes and refs kept     fails to open
section 1 middle reduced to its 0xcd byte head      fails to open
section 2 middle emptied, classes and refs kept     fails to open
```

Combined with the earlier stub ladder this bounds the remaining work precisely:
sections 0, 1 and 2 must each be emitted as real object graphs for the target
payload. Section 3 is solved, section 4 may be a four byte stub.

A template that reproduces another part's section bytes would collide with the
no donor rule, so the remaining work is emitting those graphs field by field,
which is what `MiddleBuild` already does for the expression section.

### Section 3 is generated from parameters

`re/nx/tools/RootBuild.py` emits the section 3 middle from a counter and the
seven byte anchor identity. One formula reproduces every fixture exactly:

```text
dim40.prt      counter 0x1e3  len 176  identical True
const_box60    counter 0x1e3  len 176  identical True
empty.prt      counter 0x1e3  len 176  identical True
empty_expr     counter 0x1e8  len 176  identical True
multi.prt      counter 0x1e3  len 176  identical True
sweep.prt      counter 0x1e3  len 176  identical True
```

The layout, all from named pieces:

```text
0x00  02 02 02 01 01 01 01 01      seven flag bytes
0x08  u32 counter                  document id high water mark
0x0c  32 zero bytes
0x2c  u32 counter + 49
0x30  u32 counter + 76
0x34  u32 2       0x38  u32 1        0x3c  u32 3
0x40  03 01 <len+2> "NX 2506.9120 - External User Function" 00
      08 "SYSTEM" 00   41 00   03 05 01 00   04 05 02 00
      e0 6a f8 <7 byte identity>
      fixed lane bytes and 01 01
```

The section header pointer is `header length + len(middle)`, which the generator
computes from its own emitted body, and the anchor identity may be the unset
constant `ff` times seven.

Splicing that generated body, plus the authored geometry and a stubbed section 4,
into a payload gives a part NX 2506 measures:

```text
gen_s3.prt  STATUS 0
BODIES 1, FEATURES 1, EXPRESSIONS 3
VOLUME 36000.0, AREA 7199.999999999999, MASS 0.28190304
```

Sections 1 and 0 are model dependent, not constant:

```text
section   body-less parts   one body part
1         356 bytes, 17 classes, 8 refs    1247 bytes, 30 classes, 14 refs
0         27032 bytes, 129 classes, 63 refs  28986 bytes, 154 classes, 79 refs
```

So they carry the construction and topology object graph and have to be built per
model, which is the remaining work.

### A part with an authored feature section still measures

`re/nx/tools/GeoAuthor.py` now stubs section 4 after splicing authored geometry,
so the file contains one section body generated by us:

```text
const_box60_stub.prt   56112 bytes, feature section 4 replaced by OM\x01\x01
STATUS 0
BODIES 1
FEATURES 1   BLOCK
VOLUME 36000.0
AREA 7199.999999999999
MASS 0.28190304
```

Two useful details fall out. `FEATURES 1` survives, so the feature _object_
lives in section 0 and only its record stream lived in section 4. And the
reported `p0` reverts to `40.0` while the body measures `60`, so the dimension
text also lived in section 4: measurement never depends on it.

### Which object model sections must be generated

Stubbing one section body at a time (`OM\x01\x01`, four bytes) and loading the
part in NX 2506 bounds the work:

```text
section 4 stubbed          BODIES 1, VOLUME 36000.0, AREA 7199.999999999999
section 3 stubbed          fails to open
section 1 stubbed          fails to open
section 0 stubbed          fails to open
sections 1 2 3 4 stubbed   fails to open
```

So the feature record (section 4, `UGS::FEATURE_RECORD`) is **not needed** for a
body to load and measure; it only has to exist as a well formed section. Sections
0 (topology and object classes), 1 (`UGS::CM_*`), 2 (`UGS::EXP_*`) and 3
(`UGS::OCC*`, save audit trail) all have to carry real content.

That reduces from scratch authoring to four section middles, and section 3 is
nearly constant:

```text
part            middle  classes  refs  differences from dim40
dim40.prt         176       9      2  baseline
const_box60.prt   176       9      2  0
empty.prt         176       9      2  7   bytes 0x7e..0x84
empty_expr.prt    176       9      2  9   bytes 0x7e..0x84 plus 0x08 0x2c 0x30
multi.prt         176       9      2  7   bytes 0x7e..0x84
sweep.prt         176       9      2  7   bytes 0x7e..0x84
```

Across six unrelated parts the length, the class count and the reference count
never move, and the only structural difference is the seven byte saved pointer at
`0x7e` plus a timestamp. Section 2 already has a generator
(`re/nx/tools/ExprBuild.py`), so section 3 is the smallest remaining middle to
emit from parameters, followed by 1 and then 0.

Every section body also round trips byte exactly through
`BuildSection(ParseSection(body))`, for all five sections and all four sizes, so
the record framing is fully understood; what is missing is middle generation.

An authored payload must end at the last section body. Adding two trailing bytes
after a stubbed section 4 makes NX refuse the file, while the same payload
ending at the body opens and measures.

### Payload sections resize but do not transplant

`src/convert/adapters/nx/PayloadBuild.py` now rewrites a payload with replacement
section bodies and recomputes the segment index. Replacing each body with itself
reproduces four real payloads byte for byte, and a generated expression body that
grows a section from 965 to 1263 bytes still opens in NX 2506 with
`EXPRESSION kit_len 12.5`.

Transplanting bodies between parts does not work. `empty.prt` with
`empty_expr.prt`'s bodies has the right length and still will not open, because a
body carries payload absolute references and part identity. Authoring therefore
requires generating each body for the target payload, which is what
`ExprBuild.py` does for the expression section.

### Solved: authored solids are measurable

Two conventions were missing, both now emitted by `EncodeBrepModel`:

1. every solid face must wind its outer loop **against** the surface normal
2. each edge's first fin must start at the coedge whose encoded direction is not
   reversed, not at the first coedge in topology order

With both, a box built from constants by `BuildPrism` measures correctly:

```text
60 x 30 x 20   BODIES 1, VOLUME 36000.0, AREA 7199.999999999999, MASS 0.28190304
40 x 30 x 20   BODIES 1, VOLUME 23999.999999999996, AREA 5200.0
25 x 30 x 20   BODIES 1, VOLUME 15000.0, AREA 3699.9999999999995
```

`re/nx/tools/GeoAuthor.py` now builds its body from `BuildPrism` constants and
splices the encoded stream, so no vertex, surface, curve or edge comes from a
saved document. Only the container and object-model sections are still a source
part, which is the remaining from-scratch gap.

Reversing a loop is not simply reversing its coedge list: that disconnects the
chain and the encoder refuses the model with
`B-rep loop ... is disconnected or open`. The list has to be reversed and every
coedge's direction flag flipped together, which reverses the winding while
keeping the cycle closed.

Sheet bodies are left alone. Orientation is applied only to planar faces of
solid regions, so a sheet triangle still encodes byte for byte as before.

### The attribute contract is one field: `parasolid.first_fin`

Stripping attributes one family at a time from a body NX measures gives the
minimal contract:

```text
all attributes                                              VOLUME 24000
minus parasolid.*_order on faces/surfaces/curves/edges/verts VOLUME 24000
minus parasolid.vertex_fins                                 VOLUME 24000
minus carrier_record, sense, everything but first_fin       VOLUME 24000
minus parasolid.first_fin                                   VOLUME  8000
```

So `parasolid.first_fin` on each edge is the only attribute that changes the
measurement. The rank layer, the senses, the vertex fin ring, the carrier
records and the per-entity tolerances are all irrelevant.

`parasolid.first_fin` is written as the edge's first fin, and NX's own bodies
always name the coedge whose `reversed` flag is `False`:

```text
edge 10    ring reversed [False, True]   first_fin is ring position 0
edge 24    ring reversed [True, False]   first_fin is ring position 1
edge 101   ring reversed [True, False]   first_fin is ring position 1
...8 more, no exceptions
```

Without the attribute `EmitEdgesMut` falls back to
`edge_coedges[edge][0]`, which is the reversed fin about half the time, and NX
then binds one face instead of six.

Supplying it for an authored body is necessary but not sufficient: an authored
60 x 30 x 20 box with the attribute still measures `0.0`.

### NX winds faces opposite to their surface normals

For every face of NX's own box the loop winds against the surface normal, and
for every face of `BuildPrism`'s box it winds with it:

```text
nx body      loop normal . surface normal  = -1  on all six faces
authored box loop normal . surface normal  = +1  on all six faces
```

This is the last systematic difference between the two models. It is not
sufficient on its own: flipping `same_sense`, negating the normals, or reversing
each loop with its fins gives a model whose encoded and re-decoded winding is
`-1`, and NX still measures `0.0`:

```text
authored + same_sense flipped        winding -1   VOLUME 0.0
authored + normals negated           winding -1   VOLUME 0.0
authored + loops reversed and fins   winding -1   VOLUME 0.0
authored + both                      winding +1   VOLUME 0.0
```

Everything else about the two models is identical: same vertices, same six
planes with unit normals, six faces, six loops of four coedges, twelve edges with
one curve each and one coedge per face, one closed shell in one solid region, and
the same fins per vertex. Record-list permutations, loop rotations, id renames,
plane-origin placement, curve-origin placement and edge parameter direction were
each applied to the working body and every one of them still measured `24000`.

### NX cannot re-serialise an authored body either

Asking NX to open the authored 40 x 30 x 20 part and save it under a new name
produces a rewrite of the geometry stream, and the rewrite is degenerate:

```text
auth40.prt   3393 bytes  SCH_1200000_12006  bridges 6  loops 6  points 9  curves 12  surfaces 6
   NX save as
auth40_resaved.prt 4481 bytes SCH_3701250_37102_13006
                   bridges 0  loops 0  points 8  curves 13  surfaces 6
   NX measurement    BODIES 1, VOLUME 0.0, AREA 0.0, MASS 0.0
```

Two things follow.

First, NX does not repair the body on save. It keeps the zero measurement, which
matches the earlier finding that NX never rebuilds geometry on open or on update.

Second, and more useful, NX's own writer also fails to express this body: it
drops every bridge and loop record, loses one point and invents a thirteenth
curve. A body it can measure (`dim40.prt`) keeps `bridges 6, loops 6, points 9,
curves 12` through the same round trip. So the authored body is invalid to the
kernel itself, not merely something our encoder cannot spell.

That closes the "we are emitting the wrong bytes for a valid body" hypothesis and
leaves only one: the body our encoder assembles for a model with no
`carrier_record` is not a valid kernel solid, and the shell and loop records it
derives are rejected on read. Locating that requires the kernel's own validity
contract, which is not observable through the file format.

### The doubles in the stream are plane coordinates, not tolerances

An earlier guess that the small doubles early in the stream were tolerance
fields is wrong, and the test that produced it was a false positive. Decoding
them as float64 gives `0.02`, `0.015`, `0.03`, `0.04`. With `KLengthScale =
0.001` these are the plan origins `20`, `15`, `30`, `40` millimetres. Zeroing
all 43 occurrences in a working stream drops it to `VOLUME 0.0`, but only
because it destroys the surface origins, not because tolerances matter.

Entity tolerances are written as `KMissingParam` whenever the tolerance is zero,
and the decoded model reports zero for every vertex, edge and face, so tolerance
emission is already identical between working and authored streams.

### What actually differed

Both encodings are 3393 bytes and both decode to a closed six face box with
every loop on its surface, so the visible model looked equivalent. The difference
that mattered turned out to be two orientation conventions rather than any
opaque block, and both are described above.

### Record-level comparison of a working and an authored stream

Scanning both encoded streams gives identical record structure:

```text
              working stream        authored stream
surfaces      5 6 7 8 9 10          5 6 7 8 9 10
bridges       81 82 83 84 85 86     81 82 83 84 85 86
loops         75 76 77 78 79 80     75 76 77 78 79 80
bridge 81     refs (82,1,75,4,5...) (82,1,75,4,5...)
bridge 82     refs (83,81,77,4,6..) (83,81,76,4,6..)
bridge 83     refs (84,82,80,4,8..) (84,82,77,4,7..)
```

Only the face to loop to surface pairing differs, which is the model's own
ordering. The stream header is byte identical because both come from the same
encoder, so a schema version hypothesis is out.

Every semantic check passes on the authored stream, after decoding it again:

```text
nx decoded        faces 6, worst loop-to-surface distance 0.0, bad vertices 0
authored model    faces 6, worst loop-to-surface distance 0.0, bad vertices 0
authored encoded  faces 6, worst loop-to-surface distance 0.0, bad vertices 0
nx re-encoded     faces 6, worst loop-to-surface distance 0.0, bad vertices 0
```

So the authored stream is a well formed, closed, consistently oriented six face
box by every property this repository can observe, with matching ranks, fins,
senses, parameterization and record structure, and NX still binds no faces. What
NX checks beyond that is not visible through the decoder, which is where the
from-scratch geometry work stops without a native reference implementation.

### The link layer decides how much of the body NX sees

The decisive experiment is to strip only the link attributes from a decoded NX
body and re-encode it, keeping every coordinate:

```text
decoded NX body, re-encoded                     VOLUME 23999.999999999996
decoded NX body, carrier_record and .*_order
  attributes removed, re-encoded                VOLUME 8000.0, AREA 2400.0
authored BuildPrism body                        VOLUME 0.0,    AREA 0.0
```

`8000` is exactly a third of `24000`, and the earlier id-rename experiment also
produced `8000`. So the measurement scales with how much of the record link
layer survives, not with the coordinates: with the original links NX binds the
whole body, with none it binds part of it, and for an authored model it binds
nothing.

Encoding an authored model is idempotent, while encoding a decoded body is not:

```text
encoded authored body, decoded, encoded again    identical    (canonical numbering)
encoded NX body, decoded, encoded again          different    (source numbering kept)
```

That is the whole difference. NX's own stream carries its original attribute
numbering inside the link layer, and the encoder preserves it for decoded
models. An authored model has no numbering to preserve, so the writer invents a
canonical one, and the object model's body records still refer to the original
numbers, so nothing binds.

That reading was wrong. Splitting the strip into its two halves settles it:

```text
decoded body, carrier_record removed only        VOLUME 23999.999999999996
decoded body, parasolid.*_order removed only     VOLUME 8000.0
```

`carrier_record` is not needed at all; the `parasolid.*_order` rank attributes
are. So the binding is driven by the rank layer, not by a shared numbering with
the object model.

The measured totals are cumulative per bound face. For a 40 x 30 x 20 box the
divergence sum is `-8000` for each of the three faces away from the origin and
`0` for the three through it, so `24000` means every face bound, `8000` means one
face bound, and `0` means none.

Authored models do carry ranks, including the permuted `surface_face_order`,
`curve_edge_order` and `point_order` values, plus `first_fin`, `vertex_fins` and
`sense`, and still bind nothing:

```text
BuildPrism with ranks, fins and senses        BODIES 1, VOLUME 0.0
BuildPrism with surface_face_order = surface rank, same result
```

So a necessary condition is known (rank attributes present) but not sufficient.
The binding count behaves like a chain that the encoder breaks at a point, and
the encoder's own emitters are the only place left to look.

The rank values themselves are not special. A decoded body re-encodes with
identity ranks and still binds every face, and an authored body written with the
same identity ranks and the same fin attributes round-trips through the encoder
with identical ranks:

```text
decoded face_order          [0, 1, 2, 3, 4, 5]
authored face_order         [0, 1, 2, 3, 4, 5]
decoded surface_order       [0, 1, 2, 3, 4, 5]
authored surface_order      [0, 1, 2, 3, 4, 5]
```

Only `surface_face_order` (`[0, 2, 5, 4, 3, 1]`) and `curve_edge_order`
(`[0, 1, 11, 3, 7, 10, 5, 2, 4, 9, 8, 6]`) are permutations, and they describe the
face to surface and edge to curve pairing. An authored box whose faces each own
one surface writes the identity pairing, which is equally valid in the model,
and NX still binds nothing.

Byte-level bisection cannot settle it: mixing a working and a failing stream at
any boundary produces a file that will not load (`STATUS 1`), because the records
are positionally self-consistent.

What remains is one specific unknown: how `EmitBodyMut` numbers the bridge,
face and surface records for a model that was never decoded. That needs a
record-by-record comparison inside the emitter, because every property visible
through the decoder already matches a working body.

### Encoder-side inspection: ordering is rank driven and the model is valid

Reading the writer shows how ordering works:

```text
OrderIds(Values, Entities, "parasolid.surface_order")   sorts by the rank attribute
MakeGeomLinks                                           orders faces per surface
                                                        and edges per curve
FillBodyMut                                             partitions records per body
```

An authored model that supplies those ranks in creation order is therefore
already the sorted case, which is why setting them changed nothing. The authored
model is also topologically sound: every loop closes.

```text
nx body    loops 6, broken joins 0
BuildPrism loops 6, broken joins 0
```

Both encodings are 3393 bytes with the same record layout; they differ in
absolute values and in which record owns which numbers. NX still discards the
authored one. The remaining candidates are record-level fields the decoder does
not model, because it reconstructs the model from carrier records rather than
from the writer's own emitters.

### Authored topology: attributes, ordering and conventions are all ruled out

More probes narrow the BuildPrism measurement failure.

Attribute records are not required. Re-encoding the decoded NX body produces a
stream without any of the identifiers that NX writes:

```text
                   NX stream   re-encoded
body_id            present     absent
UGS/ObjectState    present     absent
32 hex identifiers 5          0
```

That re-encoded stream still loads and measures `VOLUME 23999.999999999996`, so
the body is measured from geometry alone.

Record ordering is not required either. Assigning `parasolid.face_order`,
`surface_order`, `curve_order`, `edge_order`, `point_order`,
`surface_face_order`, `front_face_order`, `curve_edge_order`, `vertex_fins` and
`first_fin` in model order changes nothing:

```text
BuildPrism + order and fin attributes      BODIES 1, VOLUME 0.0, AREA 0.0
```

Nor is the parameterization convention. Building the model with NX's own
conventions (plane origins at face centroids, line origins at edge midpoints,
edge parameters `+-length/2`) still measures nothing:

```text
BuildPrism + centroid / midpoint / +-L/2   BODIES 1, VOLUME 0.0, AREA 0.0
```

Every single-field and combined variant still measures `0.0`, while the same
encoder output for a decoded body measures correctly. The reversed-loop variant
is the informative one:

```text
authored box 60 x 30 x 20     volume 36000, area 7200
reversed loop variant         volume  6000, area  600
ratio                              1 / 6        1 / 12
```

`36000 / 6 = 6000` and `7200 / 12 = 600`, so the reversed variant measures exactly
one face's contribution instead of six. NX is not mis-scaling the body; it binds
only one face of the shell. The normal variant therefore measures nothing
because no face binds at all.

That pointed at shell membership, but the record scan contradicts it. Scanning
the encoded streams for bridge and loop records gives:

```text
NX stream                  bridges 6, loops 6
re-encoded NX body         bridges 0, loops 0      measures 24000
BuildPrism authored body   bridges 0, loops 0      measures 0
```

So zero bridge and loop records do not stop NX measuring a body, and the `1/6`
ratio was not missing faces. The scanner is also not a reliable oracle here,
because the stream that measures and the stream that does not look identical to
it.

Identity handling is fragile. Renaming every entity in the decoded model while
leaving its `parasolid.vertex_fins` and `first_fin` references unchanged moves
the measurement from `24000` to `8000`:

```text
encoded decoded body                 VOLUME 23999.999999999996
same body, entity ids renamed        VOLUME 8000.0, AREA 2400.0
```

The rename leaves those fin references pointing at the old ids, so the encoder
loses part of the fin chain and NX measures a fragment. Authored ids that update
every reference still measure `0.0`:

```text
BuildPrism with sldprt-style ids     BODIES 1, VOLUME 0.0, AREA 0.0
```

What is left is the encoder's handling of a model that has no
`carrier_record` attributes: the decoded body carries per-record chain links,
and the encoder orders geometry records through them. An authored model has no
links at all, and every id scheme tried so far still measures nothing.

### A parametric body write is accepted and measured

Scaling the decoded model keeps those attribute records, and then the spliced
geometry is measured correctly. `re/nx/tools/GeoAuthor.py` scales the vertex
points, surface origins, curve origins and edge parameters, encodes the model,
splices the stream, reseals, and rewrites the matching expression and feature
dimension.

```text
authored_body60.prt  source 40, authored 60
  BODIES 1, FEATURES 1
  EXPRESSION p0 60.0, p1 30.0, p2 20.0
  VOLUME 36000.0, AREA 7200.0, CENTROID (30, 15, 10), MASS 0.28190304

authored_body25.prt  source 40, authored 25
  BODIES 1, FEATURES 1
  EXPRESSION p0 25.0, p1 30.0, p2 20.0
  VOLUME 15000.0, AREA 3700.0, CENTROID (12.5, 15, 10), MASS 0.1174596
```

Both match the analytic values exactly, and the write goes through Kit's own
Parasolid encoder and zlib framing, not through NX.

What is still inherited rather than authored: the topology and the NX attribute
records that come from the source body. Reproducing those records for an
authored topology is the remaining step before a part can be built from a neutral
spec with no source document.

### A first expression can be added to a part that has none

`re/nx/tools/ExprBuild.py` takes a part with no expressions, an expression name,
and a value, and emits a part that NX 2506 reports as having that expression. It
does not slice a saved middle: the section-2 middle is emitted by `EmitOne` from
the flag rule, offset list, count words, anchor block, occupancy lane, default
group record, and expression record, and the class and reference lanes are
emitted from `re/nx/tools/ExprSchema.py` (seventeen class declarations and five
references).

```text
first_expr_6.prt    EXPRESSION kit_block_len 6.0
spec_ratio.prt      EXPRESSION ratio 0.75
spec_width.prt      EXPRESSION width 40.0
spec_length.prt     EXPRESSION length 100.0
```

All four load with `unloaded 0` and report zero bodies, because only the
expression section was authored.

Two fields decide whether the part loads:

- The section pointer is the offset of the record area, that is
  `header_length + len(middle)`. It has to be recomputed whenever the expression
  name length changes. Leaving a stale pointer produces
  `corrupt data found when loading an OM file` (580044).
- The seven bytes after `e0 6a f8` in the anchor block are a saved pointer value,
  not free identity. Zero gives `found bad saved pointer value in file` (580143),
  and a random value such as `11 22 33 44 55 66 77` gives the same. Every
  single-bit mutation of a real value loads, and `ff ff ff ff ff ff ff` loads and
  means unset, so the encoder writes all ones.

What is still captured: the base part. Sections 0, 1, and 3 of the source part
are carried through unchanged, and their middles are not yet generative. The
seven-byte anchor value is also not derived; it is written as the unset
constant.

### Middle regeneration: three of five structures solved

`re/nx/tools/MiddleBuild.py` regenerates parts of the section-2 middle from
parameters and is validated against the saved corpus.

The leading flag run depends only on the object count `n`:

```text
n = 0     02 02 02 02 02 02 02 01 01 01 01 01 01
n = 1     02 02 02 02 02 02 02 02 02 01 01 01 01 01 01 01
n = 8     02 02 02 02 02 02 02 09 09 01 01 01 01 01 01 01
n = 40    02 02 02 02 02 02 02 29 29 01 01 01 01 01 01 01
```

that is seven `02` bytes, then `1 + n` twice, then seven `01` bytes, with the
`1 + n` bytes merging into the leading run when `n = 0` or `n = 1`.

Validated results:

```text
n = 0 whole middle from parameters            337 -> 337  exact True
n = 1 occupancy lane                          82 bytes     exact True
n = 1 default-group block                                   exact True
```

Not yet generative for `n >= 1`: the head still carries a layout-derived offset
and the per-object offset list plus count words, which grow with `n`.

### The middle tables are mandatory in both directions

Stripping the single object out of the seventeen-class save, keeping its class
lane, clearing the occupancy lane back to the empty trailer, and shifting every
middle offset by the removal delta also fails:

```text
seventeen classes, zero objects, generated trailer  -> 580044
```

So the per-class and per-object tables in the middle are not optional padding.
They have to be regenerated whenever the class count or the object count
changes, in either direction. Together with the earlier results this rules out
every shortcut:

```text
add classes only                      580044
add classes and shift offsets         580044
add classes and the occupancy lane    580044
remove the object from a template     580044
```

What remains is a genuine encoder for the section-2 middle tables, which is the
research programme described above, not a formatting detail.

### Class tails carry one-based ordinals

Decoding the three tokens of every class declaration shows the base token is a
one-based ordinal into the class lane of the same section. Comparing the same
class across the fourteen-class and seventeen-class saves proves it: every base
above the insertion point shifts by exactly two.

```text
class                 base (14 classes)  base (17 classes)
UGS::OM::TaggedObject        10                12
UGS::OM::StorableObject      11                13
UGS::OM::VersionedObject      9                11
UGS::OM::SubObject           11                13
UGS::OM::Set                  9                11
```

The reference token is a one-based ordinal into the reference lane, which is why
`UGS::EXP_expression` uses `5` once `UGS::ModlUtils::CachedWaveLinkData` becomes
the fifth reference.

Remapping those ordinals by parent name still does not make the part load, so
the class lane is not the only coupled structure:

```text
tokens copied verbatim                                            -> 580044
bases remapped by parent name                                     -> 580044
bases remapped, existing tails untouched, middle offsets shifted  -> 580044
```

The middle carries per-class tables sized from the class count, so a class
cannot be added without regenerating those tables at the same time.

### Class insertion is rejected on its own

Bisecting the template-free attempt shows the class lane is the failure point,
not the occupancy lane:

```text
three classes appended, counts and reference updated, middle untouched  -> 580044
three classes inserted at index 8, same                                 -> 580044
same plus every middle field pointing into the middle shifted by the
  class-lane growth (+143 bytes, 8 fields patched)                      -> 580044
```

So adding a class cannot be done by concatenating a declaration and fixing
offsets. The declaration tails carry base-class and reference tokens
(`81 f4 11 ...` for `UGS::EXP_expression`, `65 0f ...` for
`UGS::ModlUtils::CachedWaveLinkData`, `81 90 0e ...` for `UGS::EXP_generic`),
and those tokens only decode against the class ordering that produced them.

That ordering is part of the class registry contract, so an authored schema has
to be self-consistent end to end: ordinals in the tails, ordinals in the middle
index tables, and the occupancy lane all have to agree.

### The lane is regenerable from four parameters

The occupancy lane is fully determined by the occupied slot index, the object
id, the class marker, and the live count `n`:

```text
01 21 <33 slots> 21 <32 class bytes> <1 + n> 21 01 00 01 11 02 02 01 02 41
```

Building it for the one-expression save with slot 24, id `c4 71 97 78`, marker
`44`, and `n = 1` reproduces the captured lane byte for byte:

```text
actual lane tail len 82 built 82 equal True
```

Object ids are allocatable rather than fixed. Replacing the id with `c4 00 00
01`, `c4 aa bb cc`, `c3 34 50 5f`, `c0 00 00 01`, `c5 00 00 01`, and `de ad be
ef` all load, while `11 22 33 44` and `ff 00 00 01` fail with 580504. The first
byte is a bounded tag and the remaining three bytes are free.

Generating the lane for a part that had no expressions still fails. Both class
orders were tried against the template-free lane and record:

```text
three classes appended at 14..16, marker 0x4a   -> 580044
two classes inserted at index 8, marker 0x44    -> 580044
```

So the remaining gap is not the lane: it is the class-declaration tails, which
carry base-class and reference ordinals, and the object state block that has to
agree with them.

### The occupancy lane is a slot table

Between the four `EXP_hash_*` names and the `Default Group` record sits an
occupancy lane. Its shape across the three saves:

```text
expressions  lane
0            01 21 01 00 01 11 02 02 01 02 41
1            01 21 (24 x 01) c4 71 97 78 (8 x 01) 21 (24 x ff) 44 (7 x ff) 02 21 01 00 01 11 02 02 01 02 41
8            01 21 8b 80 8b 81 (22 x 01) 8b 7a .. 8b 7f 01 21 44 45 (24 x ff) 46 47 48 49 4a 4b 09 21 01 00 01 11 02 02 01 02 41
```

`01 21` opens a slot table with `0x21 = 33` slots, and `33 = class count + 16`
for the seventeen-class saves. Each slot is one of:

```text
01                    free
HH LL                 occupied, two-byte handle
HH LL LL LL           occupied, four-byte handle
```

Decoding the two seventeen-class saves by slot gives exactly 33 entries each:

```text
1 expr   (24 free) (1 x 4-byte c4 71 97 78) (8 free)             = 33
8 exprs  (2 x 2-byte) (24 free) (6 x 2-byte) (1 free)            = 33
```

A second table follows the next `21` and has 32 entries, mixing `ff` and
two-byte handles. A trailer `<1 + n> 21 01 00 01 11 02 02 01 02 41` closes the
lane, which matches the live count decoded above.

The lane is therefore an allocator state keyed by class count, not a per-object
list. Writing it needs the free-list order and the handle values that the object
records will use, so it has to be produced together with the object state
block.

### Section 2 state lane encodes live counts

Three saves with zero, one, and eight expressions show the state lane prefix
carries live counts that scale with the expression count:

```text
expressions  bytes at lane +10   bytes at lane +34/+46
0            02 13 09            01 01 01 01 1e 01 00 01 01 01
1            02 13 0a            01 01 02 01 1e 01 00 01 01 02
8            02 13 11            01 01 09 01 1e 01 00 01 01 09
```

So the first count is `9 + n` and the repeated pair is `1 + n`, where `n` is the
number of expression objects. Those are the only two prefix bytes that change
with `n`; the rest of the prefix is a ten-byte identity value and fixed lane
markers.

The tail that follows the four `EXP_hash_*` names is an occupancy bitmap over
classes and objects. It does not scale with `n` alone: it interleaves class
ordinals that have instances with literal `01` bytes, and object handless such
as `8b 80`, `8b 81`, `46`, `47` in the eight-expression save.

### Adding an expression to a part that never had one

The section 2 delta between a part with no expressions and a part with one is
now measured. Classes are not appended blindly: NX inserts two of them at index
8 and appends the third.

```text
index 8  UGS::EXP_expression                 81 f4 11 50 1c b9 b1 31 ab 22 41 05
index 9  UGS::ModlUtils::CachedWaveLinkData  65 0f ed df c5 d7 28 46 03 ec 01
last     UGS::EXP_generic                    81 90 0e cf c3 b4 e4 ee a8 d5 95 02
ref      UGS::ModlUtils::CachedWaveLinkData  07
counts   (6, 1, 0, 14, ...) -> (7, 1, 0, 17, ...)
```

Inserting at index 8 renumbers every later class ordinal, so the middle lane has
to be regenerated with the new numbering.

Appending the record and the class declarations without touching the state lane
fails with `Corrupt data found when loading an OM file` (580044), even with the
counts and the section pointer updated.

The middle grows by 155 bytes, decomposed as:

```text
offset list    6 -> 7 entries                 +4
count words    7 -> 8 words                   +4
state lane     155 -> 287 bytes             +132
  of which a 32 byte class bitmap with a 4 byte id
  a 45 byte object state block
  a 52 byte expression record
```

So an authored expression needs all five structures regenerated together.

### An expression is authored from a neutral spec

`re/nx/tools/ExprAuthor.py` takes a template part, an expression name, and a
numeric value, and emits a part that NX 2506 reports as authored:

```text
name        value   result
block_len   4.5     STATUS 0, EXPRESSION block_len 4.5
kit_two     12.5    STATUS 0, EXPRESSION kit_two 12.5
```

The name may change length. The record is the last item in the middle lane, so
the name length byte at `marker - 1` and the section pointer move by the same
delta. Rewriting with the original name and value reproduces the template byte
for byte, which proves the transform only touches the intended fields.

The value uses the handle encoding above. The template still supplies the
record skeleton, the three expression classes, and the reference, so a record
built without a template is still open.

Current status: the expression section can be produced from a name and a value,
but the base part still comes from a saved document. The class and reference lanes are emitted from a table and the
middles are reproduced from a lane, but the table and the prefix and state bytes
of sections 0-2 are still derived from a document, so this is research and not
shippable under the donor rule. No body, feature, or expression record has been
authored, and the production writer still requires a retained SPLMSSTR payload. A section begins with an optional `c0 d1 f1 ed`
separator, `ff ff ff ff`, four zero bytes, a big-endian payload size, and the
`OM 01 01` signature. Section bodies contain the NX object-model class
registry, attribute registry, object records, feature history, expression
records, and assembly records.

A compressed wrapper starts with `marker:u32 LE` and
`compressed_byte_len:u32 LE`. Marker `0x80000000 | extension_length` has an
eight-byte fixed header. Marker `0xa0000000` has a sixteen-byte fixed header.
Marker `0xc0000000 | extension_length` selects a 33, 45, or 57 byte fixed
header from its code and version words. The checksum-valid zlib member starts
after the wrapper. NX stores Parasolid binary data in that member.

## Object model

The class registry is a sequence of length-framed records:

```text
06  name_len:u16  class_name  version:u32  base_len:u16  base_name  class_id:u32
```

The attribute registry uses tag `07` and adds the attribute name and attribute
id. Object records refer to class and attribute ids. The reader retains the
registry markers and exact section bytes rather than claiming a complete typed
decode of every class.

Feature history sections carry ordered operation headers. A header starts with
`80 cd 01 04 01`, a shifted binary64 value, `ff ff`, four object-index slots,
and an optional length-framed label. The label identifies operations such as
`SKETCH`, `UNITE`, `SUBTRACT`, `INTERSECT`, `MOVE_FACE`, `CYLINDER`, and
`MOVE_OBJECT`. The four slots address object records in the section. Boolean
operations add a target list and a tool list. Expression records use the
`UGS::EXP_expression` marker.

The controlled `block.prt` control has a `BLOCK` operation and six expression
objects. NX reports `p0=40`, `p1=30`, `p2=20`, `length=40`, `width=30`, and
`height=20`. The neutral reader exposes the retained native graph, but it does
not yet project those expression values into independent neutral parameters.

## B-rep geometry

The compressed Parasolid stream in the block control begins `PS` and carries a
transmit-file description with schema `3701250`. The existing Kit Parasolid
decoder reads it as one body with six faces, twelve edges, and eight vertices.
NX reports the same body, volume `23999.999999999996 mm3`, area `5200 mm2`,
centroid `(19.999999999999996, 15, 9.9999999999999982)`, and mass
`0.18793536 kg` for the block control.

The NX process rebuilt the live feature tree after changing the `length`
expression from `40` to `45`. The body changed to volume `27000 mm3`, area
`5700 mm2`, and centroid
`(22.500000000000004, 15.000000000000002, 10.000000000000002)`.

NX stores analytic surfaces and curves as Parasolid records. The supported
families documented by cadmpeg and observed in the corpus are points, lines,
circles, ellipses, planes, cylinders, cones, spheres, tori, B-surfaces,
B-curves, trimmed curves, offset surfaces, and blend surfaces. Topology uses
BODY, REGION, SHELL, FACE, LOOP, FIN, EDGE, and VERTEX records with big-endian
fields. Geometric doubles are metres; Kit converts them to millimetres.

## Why the format was difficult

1. The `.prt` extension is shared by NX and Creo, so the envelope cannot be
   selected from the suffix.
2. NX uses both OLE and SPLMSSTR envelopes, and the modern envelope has a
   reserved header trailer with its own checksum coverage.
3. The part payload is a segment index, object-model sections, and compressed
   Parasolid streams, not a single contiguous record table.
4. The object model uses class and attribute registries, length-framed object
   records, shifted binary64 values, and object-index encodings.
5. Feature history, expressions, placement, and B-rep topology use separate
   record families and reference namespaces.

## Current implementation boundary

The production reader parses both envelopes, extracts the native stream map,
decodes Parasolid geometry through the existing Kit reader, retains the exact
native document, and exposes the native feature graph as one imported step. The
production writer
rebuilds the SPLMSSTR directory from parsed streams, supports equal-length
native attribute replacement and whole-stream replacement at any byte length,
and reseals the header and footer after every rewrite.

It does not author a new NX part from a neutral model, does not emit new NX
feature records, and does not project NX expressions into neutral parameters.
Those are the remaining gaps to the full acceptance criterion.

The reader refuses to claim parametric history: the feature step uses the
`imported` kind, so capability inference does not report `parametric_history`.
It does accept neutral edits away from the retained native graph: the writer
compares a stored projection digest and raises when features, parameters,
bodies, sketches, planes, or selections changed.

Legacy compound parts keep attributes and the object model but return no B-rep
and record `nx.legacy_geometry_unavailable`. Their payload streams are not
decoded, so a write is refused instead of converting to a modern container.
