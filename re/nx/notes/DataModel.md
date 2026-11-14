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

Current status: the class and reference lanes are emitted from a table and the
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
