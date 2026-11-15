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
