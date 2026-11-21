# Imported face identity in SOLIDWORKS 2026

This is the ordinary fresh `moBaseBody_c` path for task
`B04-SW2026-IMPORTED-BODY` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
It uses the independently pinned `34.5.2.0604` image and six disclosed
native parts. The box reference, different box, two renamed box saves and
two analytic cylinders preserve the same face attribution families.
[Named sources](../measurements/2026/ImportedBodyNamesContrast01.json)
· [Topology sources](../measurements/2026/ImportedBodyTopologyNative01.json)

## Primary attribution

The `moBaseBody_c` primary vtable at `0x180492e28`, slot `0x25e8`, selects
`sldmopartu.dll` `0x1802ff470`. With `f314` clear, its tail dispatch
through import slot `0x1803e7168` reaches
`moBodyFeature_c::iAssignFaceIds` at `0x4b784a50` in `sldmodu.dll`.
The routine initializes a fresh face callback counter at zero. The
`moFaceNotAssigned` predicate limits assignment to faces without an ID.
The geometry traversal reaches `sldgciParau::getFaces` at `0x32fd90b0`
and the known `PK_BODY_ask_faces` solid-shell enumeration.
[Kernel traversal owners](ParasolidBodyTraversal2026.md)

The callback at `0x4b786fc0` uses `makeSimpleSurfaceId` at `0x4c6d48c0`
and `moFace::assignId` at `0x4be97940`. The factory installs the
`moSimpleSurfIdRep_c` table at `0x4cf695d0`. Its `+0xd0` slot points to
`0x4c6cbb20`, which writes family code 77 at `0x4c6cbbcd`. The primary
integer fields are code 77, actual producer feature ID, the producer's
first creation-log epoch, feature-reference flags with bit `0x10`
cleared, and the zero-based constructor ordinal. The feature creation
log agrees in both headers of all six disclosures. The feature-only and
explicit body renames preserve creation time while advancing their later
update times. [Creation-log owner](ModelConstruction2026.md#feature-reference-creation-time)

| Exact code interval | SHA-256 |
| --- | --- |
| `sldmopartu` fresh dispatch `[0x1802ff470, 0x1802ff481)` | `0621e92cace2ec318177ffddbca3c1e36a73c7ca16b6a9f50a48ab69f3aee308` |
| `sldmodu` callback `[0x4b786fc0, 0x4b7870b7)` | `ad349a703dea7752d3d6beec404651e80defda26303905624e07d1380610ead4` |
| `sldmodu` factory `[0x4c6d48c0, 0x4c6d4955)` | `82e9257b91dfa27f46ffc7eda86b5cfe171bcbfac40c0590b37af58a1cb9dc72` |
| `sldmodu` primary builder `[0x4c6cbb20, 0x4c6cbc0b)` | `61ec5370ad7fa285313b53c5f72edf5da4fc122a3864bee5ce27fd5031de227c` |

## Auxiliary face identity

The BaseBody setup helper at `0x1802ff490` calls primary assignment and
then `iPostFaceIds` at `0x4b785ca0`. The callback at `0x4b78a620`
calls `moFace::assignUniqueId` at `0x4be97a70` and then `gc_AssignSurfId`
at `0x43b387c0` in `sldgcu.dll`. The feature's `FACE_ID_2001` fourth
slot contains an independent auxiliary ID and encoded model reference.
`makeFaceIdAttribute` at `0x43b39bb0` uses an explicit nonzero ID or
allocates from the process counter at `0x4415bc10`. A null local model
reference gives zero in the second word. The first word follows the
one-based shell order in the six single-body disclosures. The allocator
and prior runtime ownership govern it when other faces already exist.

| Exact code interval | SHA-256 |
| --- | --- |
| `sldgcu` auxiliary attribute `[0x43b39bb0, 0x43b39e5b)` | `42a9be36ddd82c56294365d6c6bc308aff93cccd680a1fcc56c76d619285c855` |

The plain static source comparisons use the original PE sections rather
than decompiled listings. REA verification identities for those images
are `ev_fe3c1b29426e0cccec84388e423ae3a8bfc69b5ae31ece15ccd061e4bae5a4e9`
for `sldmopartu`, `ev_7fc3ecfa02cbbd7d6067ca5c370b778582e5ddc85ae1940285a50b90bfc6ceec`
for `sldmodu` and `ev_18d55c1f2a89652d4507a3c12ef42f9f354de326dd2fd0132085ca3ea8434661`
for `sldgcu`. The independent static evidence establishes the field
owners. A generated import still requires native validation of the
allocation lifecycle, definition links and persistent selected-face
resolution.
