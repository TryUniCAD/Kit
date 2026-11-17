# Empty Parasolid partition and delta grammar

The disclosed SOLIDWORKS 2026 SP05.2 `E0_empty.SLDPRT` has zero bodies and one
`Contents/Config-0-Partition` stream containing two framed payloads. The first
holds the active `WORLD`. The second links the partition to its current and
initial partition marks and stores the earlier `WORLD` state. Disclosed A07,
A12, A13, and A14 assemblies have no partition stream. The A13 and A14 child
parts use the same two-payload format with body and attribute data.
[E0 native source and zero-body measurement](../v2026/corpus/ladder/Manifest.json)
[Prior cache admission](LegacyParasolidEmission2026.md)

The [research encoder](../../tooling/sw2026/builders/EmptyPartition.py) constructs
both payloads from the two-mark history and the transmit format. It uses the
[existing neutral binary and zlib primitives](../../../src/convert/Geometry/Parasolid.py).
It is currently a closed study of empty geometry and an initial-to-current
rollback. The preserved public blank writer and the research document composers
continue using their existing call paths. Native load, edit, or save acceptance
of newly generated files remains open.
[Populated rectangle schema and rollback comparison](PopulatedPrismPartition2026.md)

## Format selection and framing

| Input or rule | 2026 default | Authority |
| --- | --- | --- |
| Modeller build | `3701250` | Kernel getter `0x1814306f0`. The text description writer calls it at `0x1819f0616`. |
| Schema version | `37102` | Kernel getter `0x18143e4b0`, called by the schema name formatter at `0x180a17916`. |
| Embedding base | `13006` | Schema name formatter `0x180a17925`. The base node table is at `0x184543880`, initialized at `0x1820491d0`. |
| Maximum node types | `239` | Two-byte field written by the embedded-schema branch at `0x1819f08e4`. |
| User field size | `0` | Four-byte field after the node-type limit, emitted at `0x1819f0988` onward with user fields disabled. |

The header is `PS\0\0`, a big-endian u16 description length and description,
and a big-endian u32 schema-name length and schema name. The description uses
the selected `partition` or `deltas` purpose and the modeller build. The
schema name is `SCH_{modeller}_{schema}_{embedding_base}`. After that name,
write the optional embedding limit and the user field size in the order above.
`PS\0\0` selects neutral binary with big-endian integers. The compatibility
comparison uses `3601228`, `36001`, `13006`, and `231` from the established
historical interface. The SOLIDWORKS archive version `19000` and feature
behavior version `370108` have separate owners.
[Siemens Parasolid XT Format Reference, “Embedded schemas” and “Physical layout”](https://ww3.cad.de/foren/ubb/uploads/schulze/XT_Format_April_2008_tcm73-62642.pdf)
[Feature behavior version derivation](ModelConstruction2026.md)

SOLIDWORKS sends the native save through `gciPartition_w::save` at
`0x3305bca0` in `sldgciParau.dll`. The call at `0x3305be92` reaches the
kernel's `PK_PARTITION_transmit`. Its partition and delta transmit routes
reach `DS_transmit` at `0x1819e65d0` with their separate descriptions
(`0x1808ed1de` and `0x1808f2a16`). The SOLIDWORKS wrapper supplies a
little-endian framed length, wrapper signature, uncompressed and compressed
lengths, a level-1 zlib member, and eight zero bytes. The two framed sections
are adjacent, with the partition first. The research writer reuses
`EncodePartData` for both sections.

The licensed x64 kernel SHA-256 is
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`
(REA `ev_50353c50426719110196bdf9be8b6cae2180ebfacb21874fae91172c1843194f`).
The bridge SHA-256 is
`96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`
(REA `ev_fa93faaf3a7c8fc4e87b9931e8f9e289175fe12e3de169e1a2f1ea66c08151b8`).
Addresses use each image's preferred base.

## Partition records

The first record of each node type includes its effective schema after a
u16 node kind. If its descriptors equal the base schema, it emits u8
`255`. Otherwise it emits the current effective field count as u8 and
computes an edit sequence over the base and current arrays. A matching pair
uses `C`. A missing base field uses `D`. An added current field before a
remaining match uses `I` and its descriptor. Remaining current fields use
`A` and their descriptors. `Z` ends the edit sequence. A fixed scalar
descriptor contains a u8-length ASCII field name, u16 pointer class, and
element count zero encoded as a positive integer. Nonpointer descriptors also
carry a u8-length ASCII type code. The writer calculates the edit sequence and
name lengths. `0x1819e8f20` selects effective fields and compares the
descriptors. `0x1819e8cb0` writes a descriptor. [Siemens Parasolid XT Format Reference, “Embedded schemas”](https://ww3.cad.de/foren/ubb/uploads/schulze/XT_Format_April_2008_tcm73-62642.pdf)

`WORLD` has node kind 101 and transmit index 1. The base registration at
`0x1820525f0` has 11 fields. The current registration at `0x1814572e0`
includes 21 runtime fields, of which 19 are effective. `list` and
`appitem` are ephemeral. The following order is effective in this profile.
Pointer class denotes the allowed reference type. A null pointer has
logical index zero and binary encoding u16 one.

| Effective fields in order | Scalar types or pointer classes | Empty active state |
| --- | --- | --- |
| `assembly`, `attribute`, `body`, `transform`, `surface`, `curve`, `point` | Pointers of classes 10, 81, 12, 100, 1006, 1008, 29 | Null |
| `mesh`, `polyline`, `lattice` | Pointers of classes 1006, 1008, 222 | Null |
| `alive` | u8 logical | True for the active mark following the initial mark. The empty partition constructor writes true at `0x18093cf35`. |
| `attrib_def`, `attdef_list` | Pointers of classes 80, 74 | Null |
| `highest_id`, `current_id` | Two signed 32-bit integers | Highest retained/allocated mark ID and selected mark ID. The empty history is linear and both are the specified current ID. Save copies the partition's highest ID and the selected mark's ID at `0x1808ed113` and `0x1808ed11d`. |
| `index_map_offset`, `index_map`, `schema_embedding_map`, `mesh_offset_data` | Signed i32 plus pointers of classes 82, 82, 206 | Zero and null for the ordinary unindexed, mesh-free transmit. |

The effective schema describes the `WORLD` fields in both payloads. The
unmodified partition record writes an index after its schema and emits the
fields in table order. One terminator of kind 1 and null index follows.
`0x1819ed780` writes the node and invokes the first-use descriptor routine
at `0x1819ed95d`. `0x1819f0f60` emits the terminator.
For `E0`, the active record's `highest_id` and `current_id` start at
payload-body offsets `0xbd` and `0xc1`. In this ledger, payload-body
offset zero is immediately after the schema name.

## Delta records

The rollback model has two retained partition marks. The initial mark has ID
1, assigned in `DS__create_partition` at `0x18093cb0e` onward. Each
subsequent `DS__create_pmark` increments that partition's ID counter
(`0x181422690`) and assigns the new mark's ID (`0x18142269c`). Gaps are
allowed between retained marks. The transmit index of a node is separate from
its mark ID. The empty graph numbers its nodes in this order: `WORLD`,
`PARTITION`, current `PMARK`, initial `PMARK`. The two payloads share
the `WORLD` index. The native node writer looks up transmit indices through
`0x181e21e40`. In populated controls, the indices on the delta records advance
with the populated partition graph.

| Payload-body range in E0 | Typed structure and construction |
| --- | --- |
| `0x00–0x05` | Embedded-schema limit and zero user field size. |
| `0x06–0x10` | `PARTITION` kind 3, unchanged-schema flag, own index, current-mark index, highest mark ID as i32. The base registration binds kind 3 at `0x1820492ef`. |
| `0x11–0x32` | `PMARK` kind 4, unchanged-schema flag, own index, then the four indices `preceding`, `first_following`, `next_sibling`, and `prev_sibling`. Only `preceding` refers to the initial mark. Next come signed i32 `n_new_nodes`, `n_del_nodes`, `n_copy_mod_nodes`, and `delta_key`, the logical byte `delta_is_forward`, and i32 mark `id`. The counts are zero for empty geometry, and the stored rollback delta has `delta_is_forward` false. Current class registration starts at `0x181449860`; the base registers kind 4 at `0x182049511`. |
| `0x33–0x3c` | The empty new-node list terminator, then the deletion list's null index. An i32 count is the size of the preceding-state record list. It contains one `WORLD`. The delta packer writes these items at `0x1819ea192`, `0x1819ea4e5`, and `0x1819ea55a`. |
| `0x3d–0x114` | `WORLD` kind 101, generated first-use schema, shared index, initial state. Its constructor clears the fields at `0x181452e61` onward. All reference fields remain null, `alive` is false, and the three integer fields are zero. On this delta path each pointer is followed by a logical byte. The kernel writes the reference then compares its source index with the delta's threshold at `0x1819ee25e–0x1819ee2ac`. Every null reference satisfies the comparison. |
| `0x115–0x13d` | The preceding-state list terminator, the initial `PMARK` using the already emitted type schema, and the final terminator. The initial mark links only to the current mark with `first_following`, has zero counts and delta key, and has ID 1. The zero-key branch at `0x1819e9f1b` omits the rollback records. |

The current mark's header and the following delta list use distinct counts.
The node writer temporarily substitutes the count of transmitted changed
nodes at `0x1819f0d92–0x1819f0dc0`, then restores the in-memory count at
`0x1819f0e7f` before calling the delta writer at `0x1819f0f27`. The
on-wire header count is zero in E0, with one physical preceding-state
`WORLD` in the following list.

The current `delta_key` is an explicit history input. It is the i32 at
body offset `0x2a`, with the varying low byte at `0x2d`. SOLIDWORKS's
`gciPartitionManager::iAddDelta` at `0x32f90d50` inserts the allocated
delta object under the current process-global handle, increments the global,
and returns the allocated handle. Its initial next handle at `0x33129014`
is 1. The delta-open callback reaches this allocator at `0x32f91c12`.
E0 uses key 2, A13/A14 use key 1 with mark ID 9, L1 uses key 3 with mark ID
7, and the legacy blank interface uses key 14 with mark ID 3. This rules
out deriving it from body count, the mark ID, or the source path.

## Offline agreement

The checks generate each stream before comparison and keep the historical
interface on the comparison side. The version-bound E0 research input has
SHA-256 `eaf294476c1e998edcbf6183d77f50768f74fd509f030300c9ce7375dd7c1afb`.
Both pairs match the original decoded payloads and their entire wrapper bytes
on Python 3.14.7 with zlib 1.2.12.

| Comparison | Stream bytes and SHA-256 | Partition payload SHA-256 (307 bytes) | Delta payload SHA-256 (411 bytes) |
| --- | --- | --- | --- |
| Disclosed E0 using `EmptyHistory(3, 2)` | 578, `2538b108aab0a9b3a6d7d6a319c56da7a7d69d21f199a4778e30defada5bbce5` | `47e7343bcb7cce96604318603a1230aec3849d466b615dd01380d77516d1dfd2` | `7d927b291d56e28700c59f8e424071e78a090b6aae48de4bc2448b320a4bc46b` |
| Historical interface using `EmptyHistory(3, 14)` | 577, `97c3bc3b7aa7219186bc61dfe8e5f9f26a61e5f54853280406d9abd5ece1ad26` | `8ff1cd4d3369dd45b2f9a3bc9df280b4358d61ec38682dc605bc29c64af77942` | `adca164ebfcb9dc73683bc121e0682a0d15346e59bad67fd921febe9046ef7d8` |

Two generated states `EmptyHistory(5, 7)` and `EmptyHistory(9, 31)` kept
the same decoded structure. The former produced a 580-byte stream with
SHA-256 `d8c30553fcbe581182fd2d0f8f62bd3b3851cf87c934f313ce4bcf98362ee031`.
The latter produced a 579-byte stream with SHA-256
`0b158662fea7af8cc163dd2d76491a5c79436917ab581b6f5798512570477870`.
Relative to E0, each changes only active `WORLD` mark-ID bytes
`0xc0` and `0xc4`, and delta bytes `0x10`, `0x2d`, and
`0x32` for the partition's highest mark ID, delta key, and current mark
ID. The existing B-rep decoder reports no body. An audit hook recorded
zero file opens during emission. The traced SDK calls are `EncodePartData`,
`ParaStream`, `WriteBigIntMut`, `WritePointerMut`, and
`WriteShortMut`.

From the repository root, reproduce the two byte comparisons with:

```sh
PYTHONPATH=src:re/tooling/sw2026 python3.14 - <<'PY'
from builders.EmptyPartition import HISTORICAL_BLANK, EmptyHistory, blank_partition_stream
from convert.Geometry.Parasolid import EncodeBlankPart
from convert.adapters.solidworks.Container.Container import SldprtArchive

current = blank_partition_stream(EmptyHistory(3, 2))
historical = blank_partition_stream(EmptyHistory(3, 14), transmit_format=HISTORICAL_BLANK)
source = SldprtArchive.open("re/solidworks/v2026/corpus/ladder/E0_empty.SLDPRT")
assert current == source.require("Contents/Config-0-Partition")
assert historical == EncodeBlankPart()
PY
```

The comparison uses disclosed discovery data and a historical interface
contract. The novel states exercise typed serialization offline. Native
behavior on generated empty part documents, broader partition histories,
and the appropriate empty mark allocator inputs for document builders
require their own evidence.
