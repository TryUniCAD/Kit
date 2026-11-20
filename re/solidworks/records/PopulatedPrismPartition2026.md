# Ordinary rectangular Parasolid partition grammar

The disclosed SOLIDWORKS 2026 SP05.2 rectangular bosses have two adjacent
payloads in `Contents/Config-0-Partition`. Both use
`SCH_3701250_37102_13006`. The active payload contains a body, explicit
topology, geometry and attribute owners. The delta payload contains retained
partition marks and previous state. The [typed codec](../../tooling/sw2026/para/Partition.py)
re-encodes both payloads and the complete compressed stream byte-for-byte on
the seven disclosed controls below. The earlier generic prism uses
`SCH_1200000_12006` and has a single payload. Its native load generated a
rebuild warning in [the paired cache-open study](PrismPartitionOpen2026.md).

These results establish the effective schemas of a bounded current-format
graph and the construction of three tracking values. A fresh populated
partition still requires a neutral-to-kernel graph allocator and attachment
qualification. The typed codec serves offline comparisons, and the
existing research and public writer paths retain their established behavior.
[Generic prism experiment](PrismPartition2026.md)

## Effective schema

The kernel's base table for embedding schema 13006 starts at
`0x184543880`. It has 105 entries assigned by the initialization at
`0x1820491d0` and its registration callees. The class descriptor starts
with name and display-name pointers at `+0x00` and `+0x08`, a
transmittable flag at `+0x10`, and the runtime field count at `+0x14`.
Fields start at `+0x20` and advance by `0x30`. Each has a name pointer,
encoding pointer, transmission flag, pointer class and element count at
`+0x00/+0x08/+0x10/+0x20/+0x24` respectively. The effective comparison
at `0x1819e8f20` keeps transmitted fields and variable-array descriptors.
Count zero declares a scalar, count one declares a variable array, and a
larger count declares a fixed array. The variable array's u32 element
count precedes the node index. `ATT_DEF_ID` writes ASCII characters,
`UNICODE_VALUES` writes UTF-16 code units, and a vector is three f64s.
[Embedding and framing](EmptyPartitionGrammar2026.md)

| Current effective class | Difference from base 13006 | Current kernel registration |
| --- | --- | --- |
| `WORLD` (101) | Adds mesh, polyline, lattice, attribute-definition list and index-map fields. | `0x1814572e0` |
| `BODY` (12) | Adds lattice, mesh and polyline fields and their boundary counterparts. Changes the owner pointer class from 101 to 1040. Adds index offset, three index/map pointers, child, lowest node ID and mesh offset data. | `0x181432890`; samples `0x1814331b4`, `0x181433327` |
| `REGION` (19) | Adds `frame` (class 230) before `type` and `owner` (class 12) after it. | `0x18144b000` |
| `LIST` (70) | `list_type` becomes u8. Moves `notransmit` near the list type and orders the finger index, finger block and list block after the list lengths. Removes `size_of_entry`. | `0x181441f50` |
| `POINTER_LIS_BLOCK` (74) | Adds `index_map_offset` after `n_entries` and preserves variable entries. | Name at `0x18143808a`; field at `0x1814380ce` |
| `ATTRIB_DEF` (80) | Extends `legal_owners` from 14 to 17 logical bytes. | Name at `0x1814382a6`; field at `0x18143846d` |

Fourteen active class descriptors equal their base forms. Those classes
are `SHELL`, `FACE`, `LOOP`, `EDGE`, `HALFEDGE`, `VERTEX`, `POINT`,
`LINE`, `PLANE`, `ATT_DEF_ID`, `ATTRIBUTE`, `INT_VALUES`,
`REAL_VALUES` and `UNICODE_VALUES`. Delta classes `PARTITION` and
`PMARK` also retain their base descriptors. The
[field declarations](../../tooling/sw2026/para/Schema.py) record only
the 22 used types. The codec computes first-use encodings from both
field lists and checks them while walking an input. It computes array
sizes, headers, structural markers and wrapper lengths during emission.
Schema declarations contain field shapes and pointer classes.

## Topology and ownership

`WORLD.body` points at the solid body, and the body's `owner` refers
back to `WORLD`. The body points at an exterior void region with
`type='V'`, followed by an interior solid region with `type='S'`.
Each region has its own shell. Every face uses the solid shell in
`FACE.shell` and the void shell in `FACE.front_shell`. The two
directions have separate face-list links. The body's first shell is
the solid region's shell.

The start vertex of a native directed fin is at `HALFEDGE.other.vertex`
and the end vertex is at `HALFEDGE.vertex`. Forward and backward links
close the loop, and opposite fins share one edge with reversed sense.
All 24 native fins in each populated control satisfy
`fin.vertex == fin.forward.other.vertex`. The four-edge loops have
outward winding, matching each plane normal with its face sense.
The public SDK reads the same corners and planes but derives inward
loop order from the current-format controls. It reads the generic
legacy prism with outward loops. The raw native winding is the
reference for current-format writing.
[Wire and SDK winding comparison](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/NativeParasolidFinVertexIsTheEnd.md)

Across all six populated native controls and the generic geometry
experiment, the twelve straight edges and six planes bound the same
`40 × 20 × 10 mm` prism. The independently specified bounds are
`[-20, -10, 0]–[20, 10, 10] mm`, volume `8000 mm³`, surface area
`2800 mm²`, and centre `(0, 0, 5) mm`. The physical geometry
comparison uses the exact linked wire graph for the native sources and
the SDK geometry for the generic source.

`WORLD.attrib_def` links the attribute definitions. Each definition
references its ASCII `ATT_DEF_ID` name and declares the field data
types, legal owner classes and operation actions. Each `ATTRIBUTE`
has an explicit owner, the next and previous attributes of that owner,
the next and previous members of its per-definition chain, and
references to typed values. `BODY.attribute_chains` owns a `LIST`
with one `POINTER_LIS_BLOCK` of chain heads. Every used entry is an
`ATTRIBUTE` with no previous member for the given definition. The
block carries its used count separately from its allocated length.
For the disclosed ordinary single body, that block has 20 slots with
12 used in L1 and 13 in A13/A14. The extra chain is density.

| Attribute owner and name | Source for fresh construction | Disclosed check |
| --- | --- | --- |
| Body `BODY_MATCH` | The kernel body tag. `moAtomFeature_c::saveBodyTagForRollback` at `0x4b7157f0` takes the body from `moAtom+0x160`, records its low 32 bits at `0x4b715906`, and assigns the same value to its match attribute through the call at `0x4b715913`. | 1656 in L1, 599 in A13 and 600 in A14 at identical geometry. |
| Face `SWEntUnchanged` | `(face_tag & 0xffff) << 16 \| (update_stamp & 0xffff)`. `0x4b71a720` calls `moHeader_c::getCurrentUpdateStamp` and `0x4b71a76d–0x4b71a77c` packs and sends the result to `gcEntUnchangedAttrib_w::setStamp`. The preceding path at `0x4b71a6e6–0x4b71a6f7` gates assignment on incremental tessellation. | The low word is 118 in L1 and 132 in both A cases. The corresponding saved header counter is 120 or 134. Between A13 and A14 every corresponding face tag increases by one. |
| Face `DOWNSTREAM_FACE_ID` | The six signed words are entity ID, low and high words of update `FILETIME`, type, and low and high words of the owner key. The ordinary local branch at `0x4b5390eb` and `0x4b539179` supplies zero entity ID, type and owner key. `0x4b538ee3` samples `GetSystemTimeAsFileTime` and `0x4b538ef7` sets the downstream environment time; the local branch reads it back. The bridge at `0x32f9b560` packs the arguments at `0x32f9b5a1–0x32f9b5cd` and writes six values in field zero. | All six faces of each disclosed rectangle share the update time. Its UTC second equals the corresponding `ModelHeader.f48` in all six cases. Its fractional part varies, including 759945, 521155 and 860490 ticks in L1, A13 and A14. |
| Body `ATOM_ID_2001` | The actual atom-manager identity passed to the body, through `gcBody_w::setAtomId2` and its bridge setter. | In the three paired designs the first atom has ID 101. |
| Body `ENT_TIME_STAMP_2001` | Assign the body stamp from the model header's body lifecycle. `moAtom_c::setBody` at `0x4bcfb360` and the header allocator at `0x31a05340` supply that path. | 105 in L1 and 107 in both A cases, matching their saved `ModelHeader.f44`. That agreement is measured for these controls. |
| Body `LAST_BODY_MODIFYING_FEATURE_ID` and `SWIMPLICITBODYNAME_ID_U` | Preserve the actual last modifying feature identity and implicit body name. The name flow at `0x4bcfb829` passes a wide string to `gcBody_w::setSWImplicitBodyName`. | The job's single boss has feature ID 34 and name `Boss-Extrude1` in these three controls. |
| Face `FACE_ID_2001` | Native extrusion attribution starts at `moExtrusion_c::iAssignFaceIds` (`0x4b784bd0`). The feature-reference constructors for the end face and sketch-entity surface at `0x4c6d2630` and `0x4c6d2b00` reach the common feature-reference owner at `0x4bb5d2a0`. The exact creation binding and persistent face allocation still need closure. | Cap records use code 40 and six primary integers. Lateral records use code 74 and five primary integers. The second word equals the actual boss ID, including P0's 32 and L1's 34. The cap role is 1 at the end and 0 at the start. On lateral faces, the final word equals the sketch line's `f08`, matched by the boundary plane. |
| Body `BODY_IN_LIGHTWEIGHT_PERM`, `BODY_RECIPE_2001`, colour, translucency and density | Respect the model's lightweight, recipe, appearance and material state. Their registration and absence/admission must be established before generation. | Lightweight is present with value one, recipe is present with null field references, and the linked-child sources carry the extra density attribute at 1000 kg/m³. All controls have equal RGB components of 228/255 and zero translucency. |

[Model header update and body allocators](ModelConstruction2026.md)
[Pure construction of body and face tracking values](../../tooling/sw2026/para/Tracking.py)

## Archive attachment

The [offline comparator](../../tooling/sw2026/para/CompareRectangle.py)
decodes the typed `Config-0`, `Config-0-ModelHeader` and
`Config-0-ResolvedFeatures` alongside the partition. It verifies the
following identities for each populated control.

| Archive fields | Corresponding partition state |
| --- | --- |
| `moAtom.f180`, `moAtom.f1b0` | Both equal `BODY_MATCH`, the body tag. A13 and A14 keep their distinct tags in both structures. |
| `moAtom.f140` | Body `ATOM_ID_2001`. |
| `moAtom.f12c`, `moAtom.f130`, boss `f08` | Body `LAST_BODY_MODIFYING_FEATURE_ID`. |
| `moAtom.f19c` | The atom's display mode. The native constructor sets it to six. [Getter and constructor evidence](GeneratedRectanglePartition2026.md#native-ownership-rules). |
| `ModelHeader.f44` | Stored body stamp in this cohort. |
| `moPart.fe38.f18` | Intermediate kernel mark ID 3, the retained mark before geometry. |
| `moExtrusion.f3d0.f18` | Selected kernel mark ID 7 in the ladder and 9 in the synchronized sources. |

The earlier generative generic-cache candidate carries no `moAtom_c`
objects and no owning model or feature partition-mark records. A new
cache experiment needs both the cache and the corresponding typed
archive state. The prior paired oracle isolated the cache warning
to child initialization. These comparisons establish a difference in
archive ownership, with its exact native load condition still open.
[Controlled generic-cache warning](PrismPartitionOpen2026.md)

## Rollback and builder boundary

The delta payload starts with a `PARTITION` carrying the current mark
index and highest allocated mark ID. These agree with the active
`WORLD` history fields. Marks have their own transmit indices, the
partition's monotone mark IDs and separate delta handles. The
serialised mark order is selected, initial, then intermediate in these
populated saves. The links encode chronological order independently.

Each noninitial rollback has an empty new-record sequence, a null-terminated
list of deleted transmit indices and u16 kinds, an i32 changed-record
count, and a previous `WORLD` followed by a terminator. The preceding
`WORLD` is body-free and has the per-pointer qualifying bytes described
in [the empty partition grammar](EmptyPartitionGrammar2026.md). Its
`alive` value is true in the geometry rollback and false in the activation
rollback. The initial mark has key zero and omits the delta. The selected
boss mark reports `n_new_nodes` 165 in L1 and 167 in A13/A14. The
transmitted deletion lists have 148 and 150 entries respectively.
Every listed index and kind resolves to an active node. In all six
rectangles this list contains all active nodes other than `WORLD`,
`ATTRIB_DEF` and `ATT_DEF_ID`. Its order differs from the active
traversal. The partition delta packer `0x1819e9e80` filters its state
before transmission. Its native allocation and ordering rules still
need closure for fresh history.

Use the ordinary neutral sketch, extrusion direction and depth to build
its exact prism. Assign the solid and void uses from the graph and build
face, edge and vertex chains from adjacency. Allocate transmit indices,
persistent node IDs, body and face tags, mark IDs and delta handles in
their separate domains. Pass the model body's actual atom ID, last
modifying feature and update events through to the attribute builder.
`Tracking.py` computes body matching, per-face stamps and local
downstream words from those explicit values. It uses a Unix UTC second
and an explicit 100 ns fraction and has no clock or file access.

Next derive the native node registration and retention rules for the
constructed history, the complete face-attribution fields, and the
archive attachment constructors including the atom and mark records.
Feed the resulting graph
through the typed codec and check both payloads offline before a controlled
standalone and parent native open, edit, save and reopen. The prior
generic cache's SDK result and its warning 32 establish a useful control
for that comparison. The six populated 2026 documents here are
discovery controls of the same geometry. Fresh construction and
native acceptance remain unmeasured.

## Reproduction

```sh
PYTHONPATH=src:re/tooling/sw2026 python3.14 -m para.CompareRectangle \
  --bounds-mm -20 -10 0 20 10 10 \
  re/solidworks/v2026/corpus/ladder/{E0_empty,L1_boss,C1a_control,C1b_control,P0_plain}.SLDPRT \
  re/solidworks/v2026/corpus/assembly-synchronized/{A13SyncedSingleChild,A14SyncedRepeatChild}.SLDPRT
```

The comparator walks the disclosed field graphs, reconstructs the logical
and compressed streams and compares them with the originals. It checks
pointer resolution, rollback deletion types, analytic prism geometry, the
two shell uses, attribute-chain reciprocity and cross-stream attachment.
The observed writes of
both payloads and their wrappers opened zero files in each comparison.
Add the independently generated L1-shaped generic cache from
[the prior prism study](PrismPartition2026.md) to reproduce the earlier
SDK geometry comparison. The optional comparator artifact SHA-256 is
`024faf5e879743a6ad002a1bc4b9d748647b5d0044446a69c9c56f102ed5dd7e`.

| Disclosed control | Active nodes | Framed bytes | Framed stream SHA-256 |
| --- | ---: | ---: | --- |
| E0 | 1 | 578 | `2538b108aab0a9b3a6d7d6a319c56da7a7d69d21f199a4778e30defada5bbce5` |
| L1 | 173 | 3684 | `a89fe9ebf960d08c8d04ab08f2a1b7ff3be8c6c6236b9cb215e263069fb24459` |
| C1a | 173 | 3688 | `fd03ffed5948af55c83a6be2c882f65f8af82898baa7a1bb25583e029f82e5e5` |
| C1b | 173 | 3683 | `f8ce967e8d1a1ddeaf1071e86ad6337fc82fc2458320a5b6e326e554e87bfd3b` |
| P0 | 173 | 3688 | `009d9b2e26a9fdf51f9a88528c95825783a942b3633be16aacda9df0ef2495f3` |
| A13 child | 177 | 3729 | `31f0c3838e5754acedcb0bd00c28b73ca780c6918960d4c7c8c204acda8feede` |
| A14 child | 177 | 3729 | `6c04bf42ad4b62fa8e164bd2b17e6a60812ee9d931229f45958c5f1b1a3477b0` |

[Ladder source manifest](../v2026/corpus/ladder/Manifest.json)
[Synchronized assembly discovery manifest](../v2026/corpus/assembly-synchronized/Manifest.json)

The traced x64 module SHA-256 values are
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`
for `pskernel.dll`,
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`
for `sldmodu.dll`, and
`96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`
for `sldgciParau.dll`. Addresses use the preferred image bases.
Kernel REA evidence is
`ev_50353c50426719110196bdf9be8b6cae2180ebfacb21874fae91172c1843194f`.
Bridge REA evidence is
`ev_fa93faaf3a7c8fc4e87b9931e8f9e289175fe12e3de169e1a2f1ea66c08151b8`.
