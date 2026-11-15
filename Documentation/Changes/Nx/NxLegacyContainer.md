# The legacy container is writable where the modern one is not

## Behaviour

No writer behaviour changed yet. This entry records a measured opening for the from-scratch write
path: the modern `SPLMSSTR` container's class table is mandatory and validated (see
`NxClassTableScope.md`), but NX 2506 also opens the **legacy container**, and that container's class
table carries only data that is derivable from the vendor modules.

## The legacy container is an OLE2 file with the same stream names

Three parts in the corpus are not `SPLMSSTR`:

```text
flange.prt       310784 bytes   d0cf11e0a1b11ae1   OLE2
vise_screw.prt   102912 bytes   d0cf11e0a1b11ae1   OLE2
wave_parent.prt   80384 bytes   d0cf11e0a1b11ae1   OLE2
```

and NX 2506 opens all three, reporting geometry:

```text
FILE flange.prt       bodies 1 volume 75385.62526149699
FILE wave_parent.prt  bodies 1 volume 1000000.0000000002
FILE vise_screw.prt   bodies 1 volume 1.7805678853189086
```

Inside, the stream names match the modern container:

```text
UG_PART/UG_PART           141768   the model
UG_PART/DisplayJT          51816
UG_PART/JT                 22454
UG_PART/ExternalReferences   760
part/attrs                   525
images/preview              7881
qafmetadata                 2359
```

only the payload magic differs: `0d 01 "UGII  " <u32 version>` instead of `SPLMSSTR`. The existing
payload reader returns zero sections for it, so this is a separate container format.

## The legacy class table is the inheritance link plus one constant

At the first class name the bytes are

```text
06 0d 00 "UGS::OM::Meta"        01 00 00 00  13 00 "UGS::OM::RootObject"       37 00 00 00
06 07 00 "UGS::RM"              28 00 00 00  0c 00 "UGS::RM_part"             64 00 00 00
06 0d 00 "UGS::OM::Meta"        01 00 00 00  17 00 "UGS::OM::SaveAuditTrail"   c9 00 00 00
```

so each entry is

```text
0x06 <u16 schema length> <schema name> <u32 schema flag>
     <u16 class  length> <class  name> <u32 value>
```

Parsed over `flange.prt` (233 entries) and `vise_screw.prt` (192 entries):

```text
flange.prt      233 entries, 12198 table bytes, 99 distinct schemas
vise_screw.prt  192 entries,  9771 table bytes
the 4th byte field is constant within every schema      99 of 99
value == the registry's +0x34 for every shared class   127 of 127
```

There is **no name digest, no layout digest, no per-class code and no tail** — the four fields that
made the modern table unemittable. What remains is the schema name, a per-schema constant, the class
name and the `+0x34` value, and that value is the descriptor immediate at the class's registration
site, which is already extractable (slot `0x28`, 90 of 90 sites; see `NxClassRegistryApi.md`).

## Only the class name is validated

The legacy stream is stored in OLE2 sectors, so a same-length edit can be patched into the file
without rewriting the container. Four copies of `flange.prt` were built that way and loaded:

```text
leg_control.prt   byte copy                                           bodies 1  volume 75385.625261497
leg_value.prt     RootObject value 55 -> 54                            bodies 1  volume 75385.625261497
leg_schema.prt    schema UGS::OM::Meta -> UGS::OM::MetX                bodies 1  volume 75385.625261497
leg_rename.prt    class UGS::OM::RootObject -> UGS::OM::RootObjecX     OPEN_FAILED
```

so in this container the **class name is the only validated field**: the `+0x34` value can be altered
and the schema name can be altered, and the part still loads with identical geometry. That is the
opposite of the modern container, where a one-bit change to the per-class code or to the tail is
rejected (see `NxClassTableScope.md`).

For a writer this means the legacy class table can be emitted from the class list alone:

```text
0x06 <u16 len> <schema name> <u32 schema flag> <u16 len> <class name> <u32 value>
```

with the class names being the only values that must be the loader's own, and those are the names of
the classes the part actually uses. The schema names and the `+0x34` values should still be written
correctly — they are registration-site data — but they are no longer a gate.

## The container can be written, and NX accepts it

`re/nx/tools/OleWrite.py` writes an OLE2 file from a stream dictionary: 512 byte sectors, a mini
stream and mini FAT for streams under 4096 bytes, the correct root CLSID, and a directory built as a
balanced tree. Rebuilding every stream of each corpus part through it and loading the result:

```text
part              streams rebuilt   round trip   NX 2506
flange.prt                  17 of 17   identical   bodies 1  volume 75385.625261497
vise_screw.prt               6 of 6    identical   bodies 1  volume 1.7805678853189086
wave_parent.prt              4 of 4    identical   bodies 1  volume 1000000.0000000002
```

The volumes match the originals exactly, so the container layer is written rather than copied: NX
reads our container, our directory and our stream layout. The directory must be a balanced tree;
`Documentation/Gotchas/Conversion/NxLegacyDirectoryTree.md` records that requirement and the
five-entry experiment that isolates it.

What remains for a from-scratch part is the `UGII` payload itself, not the container and not the
class table.

## The class table is readable in Kit

`src/convert/adapters/nx/LegacyClasses.py` parses that table out of a raw legacy payload:
`LegacyTable(Payload)` returns the records and `ClassTableEnd(Payload, Records)` returns the offset
just past the last one. `ReadFrame` exposes the single-frame decode, and names are accepted as any
printable ASCII run of 2 to 64 characters because the oldest sample uses bare schema names such as
`RM` and `OM` where newer ones use `UGS::RM` and `UGS::OM::Meta`.

Measured on the three corpus payloads, with each record's value compared against the same class in
the live NX 2506 registry:

```text
payload            records   schemas   table end   shared classes   values matched
flange.prt             233        99    0x00348b              127         127 of 127
vise_screw.prt         192        83    0x002ab2              122         122 of 122
wave_parent.prt         98        32    0x001068                0        n/a
```

`TestNxLegacy` pins the framing, the extent and the rejection path on a constructed payload, so the
test carries no captured bytes.

`ReadNx` now calls it for compound containers and exposes the result as `nx.legacy_class_count` and
`nx.legacy_schema_count`. Reading the three corpus parts through the adapter:

```text
part             container   classes   schemas   om sections   bodies
flange.prt       compound        233        99             0        0
vise_screw.prt   compound        192        83             0        0
wave_parent.prt  compound         98        32             0        0
```

and the modern path is unchanged:

```text
dim40.prt        SPLMSSTR          0         -             5        1
empty.prt        SPLMSSTR          0         -             4        0
```

Legacy geometry is still not decoded, so `bodies` stays zero for those parts; what is now read is the
container, its streams, the attributes and the class table.

## The payload is a run of length prefixed object model sections

Walking the payload shows it is not an opaque record soup: each section starts with a big-endian
length followed by the same `OM\x01\x01` magic the modern container uses, at an earlier version:

```text
part             payload version   sections   section versions   classes
wave_parent.prt               41          5                  7        98
vise_screw.prt                52          5                  8       192
flange.prt                    53          4                  9       233
```

the header of each section, as measured:

```text
0x00  "OM\x01\x01"        magic
0x04  u32 big endian     version (7, 8 or 9)
0x08  u32 big endian     kind (0x21 for the oldest, 0x25 for the newer two)
0x0c  u32 big endian     flags
0x10  3 bytes            stamp
0x13  u32 little endian  platform length
0x17  platform           ascii, "Intel x86/Windows NT" or "x64/Windows NT"
      u32 little endian  part name length
      part name          ascii
      8 x u32            counts
```

the counts are the cross check that the framing is right: `counts[3]` equals the number of type-6
class frames parsed out of that same section, in every part — 98, 192 and 233.

`src/convert/adapters/nx/LegacySection.py` parses it (`ReadSections`, `ReadSection`), `TestNxSections`
pins the grammar on a constructed payload, and `ReadNx` reports `nx.legacy_section_count` and
`nx.legacy_section_versions`:

```text
flange.prt       compound   4 sections   versions (9,)   233 classes
vise_screw.prt   compound   5 sections   versions (8,)   192 classes
wave_parent.prt  compound   5 sections   versions (7,)    98 classes
dim40.prt        SPLMSSTR   0 sections   versions ()        0 classes
```

so the legacy payload reuses the modern section grammar with an explicit platform length and older
version numbers, which makes an emitted legacy section a variant of the emitters Kit already has
rather than a new format.

## The body starts with a per-class code table stored in the file

Immediately before the class frames, each section holds one little endian word per class:

```text
part             counts[3]   frames   codes   set      range     unset
wave_parent.prt         98       98      98    97     37-97    1
vise_screw.prt         192      192     192   191    77-191    1
flange.prt             233      233     233   232    73-232    1
```

the table sits exactly `2 * counts[3]` bytes before the first frame in every part, and the two
decodes agree on the count, so the layout is

```text
<u16 per-class code> x counts[3]    <type-6 class frames>    <type-7 attribute frames>   ...
```

the codes are not the frame values (0 of 98 and 0 of 192 match), and exactly one entry per file is
`0xFFFF`, the same unset marker the modern writer's session table uses.

That distinction is the point of this entry: in the modern container the per-class code is assigned
by the loading session and validated, which is why a modern part cannot be authored here. In the
legacy container the same kind of code is **stored in the file**, so a writer supplies it rather than
asking the loader for it.

`LegacyCodes(Payload)` reads that table, `nx.legacy_coded_classes` reports how many entries are set,
and `TestNxLegacy` now pins the table alongside the frames.

## Attribute names are recoverable from the modules, their class grouping is not

The suggested route was to rebuild per-class attribute lists from the vendor binaries. The first half
works and the second half does not, both measured on `libpart.dll`:

```text
AddAttribute imports in libpart.dll                                   0
class registrations via the registrant constructor                   1538
attribute id initialisation sites  lea rdx, [name] ; call UString ctor
names read at those sites           partitionMembershipProperty, piecePart, position, positionControl
libpart exports whose name contains AttId                               1
```

so the module never imports `AddAttribute`: each attribute id is a static `UString` constructed from
a literal, and those literals are readable at the call sites. What is missing is which class each
one belongs to. The id objects are module internals, not exports, so the export table does not carry
the class, and the initialisation sites are not adjacent to the class registrations in the sampled
regions.

Recovering that grouping is the remaining step of the suggested route. Enumerating functions through
`.pdata` narrows it but does not close it:

```text
functions calling the registrant constructor                1538
functions among those holding lowercase_underscore strings     0
attribute id initialiser stubs (UString ctor with a name)    3261
```

the 1538 registration functions contain no attribute names at all, so the binding is not local: each
attribute id is a separate 0x28 byte initialiser stub that fills a `.data` object.

The obvious mechanism for that binding was then tested directly: for every registration function, take
each `lea r8`, `lea r9` or `lea rdx` of a `.data` or `.rdata` address inside the function, read the
first sixteen pointers at that address, and check whether any of them is one of the id objects the
stubs fill.

```text
id objects with a resolved name                        591
registration functions referencing a table of them       0  of 1538
```

so the ids are not passed to the registrant as an array of id objects either. Two mechanisms are now
excluded — a local registration function carrying its attribute names, and a per-class pointer array
of id objects — and what remains is a less direct route, such as ids resolved through a helper call
at load time or registered when a class is first instantiated. Either way it is loader-time data
rather than a table this branch can read out of the module statically.

## The object data is a byte-packed id stream, not entries or length-prefixed records

Walking the bytes after the third typed entry (0x19df in section 1) rules out both candidate
grammars immediately:

```text
16-byte typed entry at 0x19df   id 196610  type 0xffff  flags 0xffff   BREAK
length-prefixed record at 0x19df  length 196610, past the section end   BREAK
```

What is there instead is a byte-packed sequence of small integers separated by variable-length
`ff` padding. The first 0x200 bytes yield

```text
2 3 4 5 6 7 8 9 10 18 26 31 32 33
```

and the region as a whole is 4.1 percent `ff` (2031 of 49105 bytes) in 567 alternating runs, so the
padding is not a fixed-size slot table either. The values are all below the 98-class count, which
makes them candidate class or object indices, but they are below the per-class code range (37 to 97)
recorded earlier, so they are not those codes.

## The header is 15 bytes followed by exactly three typed entries

Parsing the bytes after `kokr` as `<u32 id> <u16 type> <u16 flags> <u32 v1> <u32 v2>` entries of 16
bytes, starting 15 bytes after the marker, gives the same three-entry table in every section:

```text
section 1  id 273 type 1 flags 0x000f v1 0x42c05939 v2 0x39876a0b
           id 314 type 2 flags 0x000f v1 0x42c05951 v2 0x2dab048d
           id 314 type 3 flags 0x000f v1 0x0000013b v2 0x00000003
section 2  id  31 type 1 flags 0x000f v1 0x42c05939 v2 0x4c4a1338
           id  32 type 2 flags 0x000f v1 0x42c05951 v2 0x64933446
           id  33 type 3 flags 0x000f v1 0x00000022 v2 0x00000003
section 3  id  37 type 1 flags 0x000f v1 0x42c05939 v2 0x17cb256e
           id  38 type 2 flags 0x000f v1 0x42c05951 v2 0x16281ad2
           id  38 type 3 flags 0x000f v1 0x00000027 v2 0x00000003
section 4  id  43 type 1 flags 0x000f v1 0x42c05939 v2 0x66de6efe
           id  63 type 2 flags 0x000f v1 0x42c05951 v2 0x75e16345
           id  63 type 3 flags 0x000f v1 0x00000040 v2 0x00000003
section 5  id 157 type 1 flags 0x000f v1 0x42c05939 v2 0x369aa4bb
           id 310 type 2 flags 0x000f v1 0x42c05951 v2 0x1060de6c
           id 392 type 3 flags 0x000f v1 0x00000189 v2 0x00000003
```

so the header is

```text
"kokr"  00 ff ff  <f32 96.1657>  <u32>
```

15 bytes, followed by exactly three 16-byte entries, and then the entry sequence breaks (the fourth
candidate has `flags 0xffff` and `type 0xffff`). The type-1 `v1` is always `0x42c05939` (96.1743) and
the type-2 `v1` is always `0x42c05951` (96.1745), so those two fields are constants of the format, not
per-part data. The type-3 `v2` is always 3.

That is the first record grammar in the legacy object region: a fixed 15-byte preamble, a fixed
three-entry typed table, and then the object data.

## The object region starts with a fixed 27 byte header

`kokr` is not a stray string: it occurs once per section, at the start of that section's object
region, and the 27 bytes after it have three constant fields.

```text
marker   section   +7 (float)   +11 (u32)     +15 (u32)   +19          +23 (float)
0x0019a0     1     96.1657      0x404b6588    273         01 00 0f 00  96.1743
0x00df80     2     96.1657      0x0ec2029d     31         01 00 0f 00  96.1743
0x00ecc4     3     96.1657      0x7a02dfa6     37         01 00 0f 00  96.1743
0x00f3fa     4     96.1657      0x20b2da20     43         01 00 0f 00  96.1743
0x011006     5     96.1657      0x77b0bf63    157         01 00 0f 00  96.1743
```

so the header is

```text
"kokr"  00 ff ff  <f32 96.1657>  <u32>  <u32>  01 00 0f 00  <f32 96.1743>
```

with the two floats and the `01 00 0f 00` word constant across all five sections, and the two
middle words varying. The varying small integers (273, 31, 37, 43, 157) are the shape of a count or
an id, not a measurement.

`01 00 0f 00` is not a record delimiter: it occurs only twice in the whole 49168 byte object region
(0x19b3 and 0x52a2), and the second occurrence is followed by a different structure.

## The modern tag grammar does not appear in the legacy payload

The modern middle's `<tag><value>` grammar was then tested against the legacy payload, both in the
object region and across the whole file. A run is a maximal sequence of bytes where each byte is a
tag (`0x80` to `0x84`) and the value width is fixed for the run.

```text
wave_parent.prt section 1, 0x19a0..0xd9b0
  tag bytes present   0x80: 47   0x81: 12   0x82: 13   0x83: 7   0x84: 22
  longest run at any start and width   0 records

whole 71937 byte payload
  runs of 3 or more records   5
  longest run                 5 records, 20 bytes, at 0x01377
```

so the tags occur as isolated bytes, never as a run, and the longest run in the whole file is 20
bytes. That is noise, not a grammar. The legacy object region is a different encoding, and the
modern field grammar does not transfer to it.

## The modern field is a tag byte plus a width the tag selects

Reading the first records of the migrated part's section 0 middle with exact boundaries:

```text
7f                      leading byte, 127
12 "first_record_area"                 80 cf           tag 0x80, 1 value byte, 207
1c "m_calculatorRegisterValues"        84 81 80 92     tag 0x84, 3 value bytes, 9601153
0f "m_nextInstance"                    83 ef 80 92     tag 0x83, 3 value bytes, 9601263
1d "m_savedAdvancedDisplayFacets"      83 f1 80 92     tag 0x83, 3 value bytes, 9601265
14 "m_saveDisplayFacets"               83 ee 15        tag 0x83, 2 value bytes, 5614
10 "m_cachedBodyBoxC"                  11              no tag, 1 byte, 17
```

so the field is `<tag><value>` where the tag selects the width, and the width is not
`0x80 | (width - 1)`: tag `0x80` carries one byte, `0x83` carries two or three, `0x84` carries three.
The three-byte values are sequential (`9601153`, `9601263`, `9601265`), which is the shape of an id
rather than a measurement.

The legacy object region does not use this encoding: it begins `6b 6f 6b 72` (`kokr`), not a tag byte,
so the modern field grammar does not transfer to it. That is the limit of the differential.

## The differential has one shared name, and its two values are not the same quantity

Comparing the two files by attribute name gives exactly one name present in both object regions:

```text
name                 legacy bytes after it        modern bytes after it
first_record_area    cf 00 00 00 (u32, 207)       80 cf 1c
```

the other five names sampled (`m_calculatorRegisterValues`, `m_nextInstance`,
`m_savedAdvancedDisplayFacets`, `m_saveDisplayFacets`, `m_cachedBodyBoxC`) exist only in the migrated
part, because they belong to classes the legacy file does not carry.

The modern field widths, read by taking the bytes between a name and the next record's length byte,
are not constant:

```text
first_record_area              80 cf 1c            3 bytes
m_calculatorRegisterValues     84 81 80 92         4
m_nextInstance                 83 ef 80 92         4
m_savedAdvancedDisplayFacets   83 f1 80 92         4
m_saveDisplayFacets            83 ee 15            3
m_optTargetMatrix              83 ee 07            3
m_displayMarker                83 87 7f            3
m_userAttributeList            80 d0 02 02 04 06 02  7
```

so the width is not a function of the name, and the leading byte is always in `0x80` to `0x84`. The
single shared pair cannot settle the encoding either, because the two values are not the same
quantity: the legacy field is the attribute's id in that file (207), while the modern field is
whatever the migrated part assigns, and nothing in the two files ties them together.

That is the limit of the differential: one shared name, two different quantities, and a width that
varies per record. Deriving the width rule needs the attribute's declared type from the schema, which
is the next test rather than something this comparison can supply.

## The modern middle is a name and binary field stream, not a record list

The migrated part's section 0 middle begins with attribute names separated by short binary fields:

```text
0x0000  7f 12 "first_record_area" 61 80 cf 1b "m_calculatorRegisterValues" 84 81 80 92
        0f "m_nextInstance" 83 ef 80 92 1d "m_savedAdvancedDisplayFacets" 83 f1 80 92
        14 "m_saveDisplayFacets" 83 ee 15 10 "m_cachedBodyBoxC" ...
```

so the names are real attribute names and each is preceded by a byte equal to its length plus one, but the
binary field between names is not a fixed width: three bytes after `first_record_area`, four after
`m_calculatorRegisterValues`, and the widths do not follow the name length. A brute force over start
offset 0 to 5, name length `L` or `L-1`, and value width 0 to 8 parses at most **two** records before
the framing breaks.

That is the same shape as the legacy region: names and small binary fields interleaved, with no
self-describing width. It also explains why the reader carries `middle` verbatim in both containers
rather than decoding it.

## NX migrates a legacy part, which gives the same part in both formats

Opening `wave_parent.prt` and saving it produces a `SPLMSSTR` part of the same model, so both
containers can be compared on identical objects:

```text
legacy wave_parent.prt          SPLMSSTR wave_modern.prt
payload 71937, 5 sections       payload 51434, 5 sections
98 classes                      160 classes, 64 of them shared after dropping the UGS:: prefix
section 1 55056 bytes           section 0 40188 bytes, middle 32220, record area 0
```

and the payload metadata is per section rather than per part in both: `kokr` occurs 5 times in the
modern payload and 7 in the legacy one, and `NX 3.0.2.3` occurs exactly 5 times in both, matching the
five sections each file has.

Two consequences follow. First, the migrated part is a usable key for future alignment work: it is
the same model in a container whose framing is partly known. Second, it shows where Kit stands on
both formats: the modern section's objects sit in `middle`, which the reader carries verbatim, and
`record_area` is empty, so Kit decodes OM object records in neither container. Geometry comes from
the Parasolid streams, which is why reading works without that layer.

## The class-id header hypothesis fails

With the layouts available, the base class states the shape a record header should have.
`OM_object` and `OM_methodic_object` both declare three attributes only: `isa` at offset 8, size 2;
`om_object_flags` at offset 10, size 2; and `om_storage_flags` at offset 12, size 1. That is a 13-byte
header with a class id at offset 8, which makes a walker testable: read the id, look the class up,
advance by that class's extent, repeat.

Tested over `0x19a0` to `0xd9b0`, looking for any position where the little endian word is one of the
95 resolved class ids and the next word is small and the following byte looks like a storage flag:

```text
candidate triples (id, flags, storage)      218 of 49000 positions
gap to the next candidate == that class's extent    1 of 217
extents of the matched classes              24 (95 times), 48 (63), 56 (26), 128 (23)
observed gaps between candidates            6, 35, 40, 48, 50, 51, 52, 53, 54, 578, 1303
```

so the header shape does not hold in the data: the matched extents are dominated by base classes, the
gaps cluster where no class extent lies, and the walker advances exactly once in 217 tries. 218 hits
against roughly 70 expected from chance alone is not a signal either.

That closes the seventh independent test of this region, and it is the one with the strongest prior,
because it came from the schema rather than from the bytes.

## A correction: the legacy classes do resolve, and their layouts still do not segment

An earlier statement in this entry said the legacy class names do not resolve in the NX 2506 registry
"0 of 98 shared". That measurement compared them against `dim40.prt`'s 154 class names, not against
the registry itself, and it was wrong. Querying the full 7806 class registry by name:

```text
wave_parent.prt class names resolved       95 of 98
attributes per class                       0 to 47, reported for every one
```

so the layouts are available, and the extent test was repeated with them rather than with the modern
classes' extents:

```text
classes with a layout                     95
distinct extents in 4..512                41, the most common being 72, 80, 48, 36
best periods overall                      4 (0.316), 8 (0.302), 16 (0.299) - the zero run artefacts
best periods that are class extents       104 (0.266), 32 (0.266), 24 (0.265), 56 (0.260), 208 (0.258)
```

no class extent exceeds the zero-run baseline, so records are not fixed-size instances of a class
even when the correct layouts are used. That is a stronger statement than the earlier one, and it
rests on the right data.

## Class layout extents do not segment the object region

The last untried prediction was that a record is the size of its class's attribute layout, so the
region would repeat at that period. The extents come from the live registry, which reports each
class's attributes with type, size and offset; `UGS::RM_part` is 155 bytes, `UGS::RM_entity` 72 and
`UGS::OM::RootObject` 204.

Agreement was then measured for every period from 4 to 512 over `0x19a0` to `0xd9b0`:

```text
period 155 (RM_part extent)     0.248
period 72  (RM_entity extent)   0.236
baseline: period 4 (zero runs)  0.316
best overall periods            4, 8, 16, 52, 5 - all at or below 0.316
```

so records are not class-layout sized, and the best scoring periods are the zero-run artefacts rather
than any structural size. The 567 word table before the region does not help either: its values are
almost all in 0 to 14 with a maximum of 55032, so it is not a table of offsets into the object region
that would let records be located rather than walked.

## An apparent 16 byte stride in the object data breaks at the third record

Reading the object region as float32 at every byte offset turns up a tempting pattern:

```text
offset   value
0x19a7   96.1657
0x19b7   96.1743     16 bytes after the first
0x19c7   96.1744     16 bytes after the second
```

and one byte earlier the same three positions hold -3.326, -3.394 and -3.396, also 16 apart. Two
fields cannot overlap by three bytes, so at most one of those readings is real, and the fourth record
decides it: `0x19d7` holds `3b 01 00 00`, a denormal rather than a coordinate.

So the 16 byte stride is an artefact of two adjacent records, not the record size, and the float32
anchors confirm what the marker gaps already showed: no stride, and no field offset, is stable.

## The region after the attribute frames aligns, but not as a record prologue

Aligning the three parts at the end of their attribute frames shows a word table in each, and the
first words do not agree beyond a short prefix:

```text
part             attribute frames end   first sixteen words after it
wave_parent.prt              0x00109e   1 1 0 0 1 1 1 1 1 1 1 1 8 8 5 1
vise_screw.prt               0x002ec3   1 1 4 9 1 3 15 33 12 1 1 2 1 1 7 1
flange.prt                   0x003868   1 1 11 13 1 3 15 41 16 11 1 6 1 1 1 4
```

`1 1` opens all three and `1 3 15` appears at the same position in the two newer parts, so the first
words are a header of some kind, but the values after them are per part rather than a fixed prologue,
and `wave_parent.prt` diverges at the third word. In `wave_parent.prt` this table is bounded:
`0x109e` to `0x197c`, ending in the sequential ids `0x32 0x33 0x34 0x35`, then `01 00 00 00`, the tag
`00 02 00 03`, and the length prefixed string `NX 3.0.2.3`.

so the three parts do not share a record prologue that a walker could key on: what they share is a
short header prefix, after which the content is part specific. That is why this entry stops at the
object layer rather than proposing a walker built on a coincidence in the first words.

## The object region has no fixed stride

Two measurements bound how the object region can be walked, both over `0x19a0` to `0xd9b0` of
`wave_parent.prt` section 1:

```text
byte agreement at a candidate period, sampled every 7 bytes
  period 4     0.327      period 8     0.303      period 16    0.296
  period 52    0.289      period 53    0.282      period 51    0.275

gaps between successive 01 00 00 00 markers
  285 403 115 11434 199 70 8 44 12 16 16 4 60 8 8 4 144 4 387 578
```

no period stands out, and the marker gaps are irregular across two orders of magnitude, so the region
is a stream of variable length records rather than a table of fixed size entries. The `01 00 00 00`
marker appears 279 times and is not a record delimiter at any stride.

That is the precise reason this entry stops at the object layer: a walker for it needs the record
grammar (header, id, length, field layout per class), and neither the stride nor the header can be
inferred from the corpus without knowing the grammar that produced it.

## The object data is byte packed, not word aligned

The object region of `wave_parent.prt` section 1, from `0x19a0` to the section end at `0xd9b0`, is
49168 bytes. Measured across it:

```text
marker 01 00 00            329 occurrences, 279 of them 01 00 00 00
marker 02 00 00            102 occurrences
fill ff ff ff ff           393 occurrences
float32 in a coordinate range
  at byte offset 0         739, but the samples include 32767.748 and 32768.0 sentinels
  at byte offset 1         588, with negatives such as -256000.531
  at byte offset 2         643, samples -3.326, -3.394, -8192.0
  at byte offset 3         726, samples 96.166, 3.178, 96.174
```

so the records are not word aligned: the coordinate floats sit one byte into a group, which is why
reading the region as u32 or as aligned float32 produces nonsense. Any object record walker has to
advance one byte at a time, and the `0xFF` fill and the two marker families have to be classified
before ids and lengths can be read. That is the layer this entry stops at.

## The table after the attribute frames ends in sequential ids

In `wave_parent.prt` section 1 the region between the class frames and the object data reads, in
order:

```text
0x1068  "opt_att" then a u32 1
0x1073  the single type-7 attribute frame, ending at 0x109e
0x109e  a long run of small little endian words, mostly 1, with occasional 5, 6, 8, 12, 14, 29, 112
0x1974  0x32 0x33 0x34 0x35 in sequence, so the run ends in consecutive ids
0x197c  u32 1, then the tag 00 02 00 03, then a length prefixed string "NX 3.0.2.3"
0x19a0  object data, starting 00 ff ff dc 54 c0 42 88 65 4b 40
```

the run is about 568 words and its tail is an increasing id sequence rather than the 0/1 flags the
head carries, so it is a mixed structure rather than a flat flag array. `vise_screw.prt` and
`flange.prt` do not carry that version string: their only `NX ` text is `NX ANSI Symbols`, so this
boundary is version specific and comparing the three needs the run's tail rather than that string.

## Nothing after the attribute frames is optional

Section 1 of `wave_parent.prt` continues past the attribute frames with a 568 entry little endian
u32 table, then an ASCII version block (`NX 3.0.2...`), then the object data up to the section end at
`0xd9b0`. Zeroing each of those in place, so every offset and length stays valid, and loading the
part:

```text
mutant        bytes zeroed        result
zp_ctrl       none                bodies 1  volume 1000000.0000000002
zp_table      0x109e..0x197e      OPEN_FAILED
zp_text       0x197e..0x19c0      OPEN_FAILED
zp_tail       0x197e..0xd9b0      OPEN_FAILED
zp_attr       0x109e..0xd9b0      OPEN_FAILED
```

The control goes through the same container writer and loads with the source volume, so the failures
are caused by the zeroed content, not by the rebuild. A legacy payload therefore has no optional
tail: the table, the version block and the object data are all load bearing, and a minimal payload
cannot be produced by omission. That is why no payload has been emitted for loading — the remaining
work is to _generate_ the object data, not to trim a section down to something NX will still accept.

## The attribute frames are fully framed and tile consecutively

The type-7 frame is the class frame with one extra length prefixed name and the same trailing value:

```text
07 <u16 schema length> <schema> <u32 flag> <u16 class length> <class> <u16 attribute length> <attribute> <u32 value>
```

and the frames are adjacent, with no padding and no gaps, in every part:

```text
part             attribute frames   consecutive transitions   trailing value of first frame
wave_parent.prt                 1                     n/a   207
vise_screw.prt                 14                      13   124
flange.prt                     13                      12   124
```

That also resolves the unexplained `u32 0xcf` at `wave_parent.prt 0x109a`: it is the `value` field of
the `RM / RM_entity / first_record_area` frame, and 207 is the same value in all three parts. The
runs of `01 00 00 00` that follow are a separate structure after the attribute frames, not part of
the frame.

`src/convert/adapters/nx/LegacyClasses.py` now parses it: `ReadAttribute`, `LegacyAttrs`, and the
metadata key `nx.legacy_attribute_count`. Measured through the adapter:

```text
flange.prt       sections 4   classes 233   coded 232   attributes 13
vise_screw.prt   sections 5   classes 192   coded 191   attributes 14
wave_parent.prt  sections 5   classes  98   coded  97   attributes  1
dim40.prt        sections 0   classes   0   coded   0   attributes  0
```

## The body after the class frames is the same model in an older framing

Walking section 1 past the class frames shows the body does not switch to an alien syntax. Each
class frame is followed by its four-byte value, and then a small number of **type-7 frames** declare
individual attributes:

```text
07 <u16 schema length> <schema> <u32 flag> <u16 class length> <class> <u16 attribute length> <attribute> <payload>
```

present in all three parts, immediately after the class frames:

```text
part             type 7 frames   first four declarations
wave_parent.prt              1   RM / RM_entity / first_record_area
vise_screw.prt              14   UGS::RM / UGS::RM_part / m_legacyLineWidthConverted
                                 UGS::RM / UGS::RM_entity / first_record_area
                                 UGS::Annot::Dimension / UGS::Annot::MeasurementDimension / extracted_geoms
                                 UGS::Annot::LeaderObject / UGS::Annot::LeaderObject / m_singleSidedDimArrowLength
flange.prt                  13   the same four, then more annotation attributes
```

the attribute names are the ones the modern container carries in its schemas, so the legacy body is
the same class and attribute model expressed with a different frame type and no digests. What is not
yet decoded is the payload that follows each attribute name, and the object records that come after
those attribute frames.

## The legacy payload is a separate serialisation of the whole model

Reading the payload header and the class records shows this is not a wrapper around the modern
container, but an older serialisation with its own record stream:

```text
part             payload    version   0x14    0x16    0x18    0x1c   tail text block
wave_parent.prt    71937         41     14   12964    7738      79   yes
vise_screw.prt     82812         52     14   16356    7662      82   yes
flange.prt        141768         53     14   17305    9912      82   no
```

header layout as measured, without claiming meanings for the fields that are still unknown:

```text
0x00  0d 01                 magic
0x02  "UGII  "              signature
0x08  u32                   version (41, 52, 53 across the three samples)
0x0c  00 00 01 00           constant in all three
0x10  u32                   0 in all three
0x14  u16                   14 in all three
0x16  u16                   12964 / 16356 / 17305
0x18  u32                   7738 / 7662 / 9912
0x1c  u32                   79 / 82 / 82
0x20..0x60                  zero                       (then the record stream begins)
```

the class records follow the framing already decoded, as type-6 records inside that stream:

```text
06 0d 00 "UGS::OM::Meta"       01 00 00 00 13 00 "UGS::OM::RootObject"       37 00 00 00
06 05 00 "COLOR"               01 00 00 00 0b 00 "COLOR_table"               e8 03 00 00
06 06 00 "CUTTER"              05 00 00 00 0e 00 "CUTTER_display"            e8 03 00 00
```

and two of the three payloads end with an ASCII block:

```text
(Child) root: {
		Class; ug_base_part;
		};
```

so the legacy container holds a **second, independent serialisation of the object model**. Its class
table is understood and writable, and its container is written by `re/nx/tools/OleWrite.py`, but its
record stream is not decoded, and NX 2506 cannot save this format, so the three corpus parts are the
only samples that will ever exist here.

## Limits

- The legacy payload writer is not implemented. This entry establishes the container, the class
  table and the section headers; what is still undecoded is the body of a section after its class
  frames, which holds the object records and the geometry. Authoring a part still needs that body.
- NX 2506 does not save this container, so no new samples can be generated; the three corpus parts
  are the whole evidence base, and `wave_parent.prt` did not yield the table at the anchor the other
  two use, so its layout differs.
- `Writer.py` still raises for a neutral document. The modern container remains unwritable because
  of the validated class table, and no part has been authored in either container yet: what is
  established here is that the legacy table is not a gate, not that the legacy payload is written.
- `re/nx/examples/` holds these parts; nothing from it is copied into `src/`.
