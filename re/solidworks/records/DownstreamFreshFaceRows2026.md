# Fresh ordinary face-row operands in SOLIDWORKS 2026

This source-only checkpoint derives the ordinary four-edge face reference's inline operands and constructor scalars. Final all-face state and native cache acceptance remain unqualified. Model-context representation replacement, key ambiguity and temporary map lifetime are explicit boundaries.

Task `B04-SW2026-DOWNSTREAM-FRESH-FACE-ROWS`, owner `configuration_header`, PR #121. Root owns the prefix, surface-ID/keeper construction, shared codec, product execution and vendor oracle. The separate temporary `f30/f38/f40` collector is not changed. No CAD file or held-out input was read.

The original `sldmodu.dll` is build `34.5.2.0604`, preferred base `0x4b140000`, SHA256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The [numeric ledger](DownstreamFreshFaceRows2026.json) and [host receipt](../measurements/2026/DownstreamFreshFaceSource01.json) bind 41 complete function entries, 89 source intervals, nine actual virtual targets, two runtime descriptors and 20 typed imports. No vendor listing, binary, CAD row or native payload is enclosed.

## Selected constructor profile

The bounded case is one actual nondegenerate four-coedge, one-loop face of a classical Parasolid solid created by one ordinary boss. Its own and four adjacent surface representations are real generated owners. The special ID manager is absent, participating edges have no permanent-edge attribute, the body is neither ghost nor shrinkwrap, and the post-model-context array contains at least four distinct nonnull representation pointers. A rectangular-prism side or cap with five distinct surface owners satisfies the constructor predicate. This is a source rule, not a native measurement of a new writer.

The actual `moFaceRef_c` table is `0x4cf95ed0`; its serializer is `0x4bba9640`. The actual `moCompFace_c` table is `0x4ce05780`; its serializer is exactly the common `moCompBEntRef_c` body at `0x4bba46c0`. Both have ordinary schema 1. Native object sizes are 248 and 320 bytes; those are not wire lengths.

The caller at `0x4b52b294` requests `get(actual face, actual model, 0)`. It may discard and reconstruct the result with mode 1 at `0x4b52b2d0`. The mode predicate is applied after the factory's model-context callback, not before it.

## Six inline rows, including the separator

`0x4bc141f0` selects the actual first loop when `getLoops` returns one. It otherwise asks for the non-hole loop collection; that wider profile is not newly qualified here. For each selected loop, it retains actual `getCoEdges` order and appends a null separator. Under `gc_IsKernelParasolid()==1`, it installs:

`count = 1 + sum(len(loop.coedges) + 1 for each selected loop)`

| Inline index for the selected face | Actual operand |
| ---: | --- |
| 0 | Surface representation of the actual selected face |
| 1–4 | Each actual coedge's edge permanent representation when `hasEdgeId`; otherwise the surface representation of that coedge's actual right face |
| 5 | Null representation pointer, the retained one-loop separator |

For the selected absent-permanent-edge branch, indexes 1–4 therefore refer to the four adjacent faces. They do not contain kernel node IDs or already allocated downstream row IDs. The ordinary permanent-ID vocabulary remains independently bound by [the boundary-role proof](DownstreamBoundaryRoles2026.md).

The Parasolid branch jumps to cleanup at `0x4bc1446d`; it does not enter the other branch's null compaction. The terminal null is retained. Four geometric edges therefore give **six** inline `moEntityId_c` bodies, not five. Each inline wrapper is distinct; its representation pointer uses normal object/class framing and aliases. The separator remains an inline wrapper with a null representation pointer, not an omitted row.

The factory calls actual virtual `+0xc8` at `0x4bc12aa7`. The target `0x4b74cdf0` externalizes each nonnull ID against the actual model with mode 0. That can invoke the actual representation subtype's `+0x110`/`+0x100` and model mapping, replacing the representation pointer. This packet does not assume that every subtype is a no-op. Root's surface-identity bridge must supply the supported post-context owner and alias graph.

## Constructor scalars and embedded role ownership

The predicate at `0x4b538ca0` requests mode 1 when there are at most three inline rows, or fewer than four distinct nonnull representation pointers for a larger array. It counts pointer identity, not structural equality. Six rows with five distinct nonnull representations retain mode 0.

`0x4bc118e7` then stores qword 1 at reference `+0x60`, so the two serialized u32 words are `(f60,f64)=(1,0)`. Using the bare default constructor's `(-1,-1)` pair for that reference is wrong. The mode-1 path instead writes low32 of the actual `gcFace_w` handle into `f64` at `0x4bc118f4` and enters further candidate/ambiguity work; that handle is not derived by this packet.

For the selected mode-0, non-special constructor branch, the retained reference state is:

| Field | Source-derived state |
| --- | --- |
| `f60,f64` | `1,0` from the semantic constructor |
| `f08` | 6, computed from the actual selected loop |
| `fe8` flags | 0 for the selected classical non-ghost/non-shrinkwrap profile |
| `f70` | Constructor-zero unresolved handle cache; not a fabricated native tag |
| `f28,f30` | Constructor sentinel `1e100` |
| `f40` | No vertex-reference owner in this selected branch |
| `f48`, time count | 0, no time pairs |
| `fec` | Actual current native file-version getter |
| Face suffix `nf0,ff0` | 0, empty match array |

These are selected constructor/retained-store values, not universal final native defaults. The pre-store changes below must be accounted for.

The array installer `0x4b755540` deletes the prior inline array and explicitly deletes/clears embedded `BEnt.f18` at `0x4b755598..0x4b7555c0`. Thus the initial downstream helper created at the start of the semantic constructor is not retained unchanged through array replacement.

Each nonnull indexed face call at `0x4b74bf60` recreates `f18` under the active downstream construction scope, then attempts to insert the actual already allocated face-row ID under that inline index. Allocation lookup is nonzero-ID based. These calls occur before the current face's `f48` row is appended. Consequently:

- The current new face is absent from the row lookup during its own constructor
- Only already registered earlier face rows can supply constructor-stage adjacent role values
- The null separator has no role-map insertion
- The first face's constructor-stage role map is empty, while the recreated embedded owner is present

The new embedded owner initializes its value vector empty, `f38=0` and both trailing words zero. These are child-object fields, separate from the parent's temporary collector. A later replacement or ambiguity path must not be collapsed into this prefix observation.

## Actual component wrapper

`0x4b7e72b0` retains the actual FaceRef through the common BEnt constructor. The component at `f58` is the supplied component's actual virtual-`+0x158` clone, as proved in [the local-owner record](DownstreamLocalOwnerContext2026.md). The runtime clone and standalone wire owner remain distinct.

The body atom is copied explicitly into wrapper `f18` and `f1c` at `0x4b52b36c/36f`. It is not the row index, node ID or downstream number. The row's number consumes the shared counter independently at `0x4b52b38e/396`.

For this ordinary wrapper, CompRef initializes scalar words `f68,f20,f30,f70,f84,fa0,f34,f48` zero; `f90/f94/f98/f9c` are `-1`; all five optional owners and alias text are absent; `f4c` comes from the current-file-version getter. The BEnt wrapper stores the actual reference at `fe8` and starts optional external owner `ff0` null.

The BEnt semantic constructor transfers reference flags 4 or `0x10`, maps `0x1000` to wrapper `0x2000`, and transfers bit `0x40` while clearing that bit in the reference. The selected ordinary solid has none, so wrapper `f68` remains zero. These bit owners must not be confused with a model's unrelated flags.

Wrapper `f48` has a real conditional assignment: a candidate feature must pass virtual `+0x1c0` and have positive `+0x1e80`. The actual ordinary extrusion table's `+0x1e80` is the zero-return leaf `0x4b27cbe0`, so an actual boss-owned candidate cannot perform that assignment. This justifies zero in this profile; it does not establish zero for arbitrary feature owners.

## Changes between construction and store

The first candidate is appended and assigned an ID before `0x4b5254f0` validates it. The validator considers its original semantic key and an alternate key made by a fresh FaceRef that swaps **only inline indexes 1 and 2** (`0x4b757970`). It is not a geometry sort.

When earlier key state is found, `0x4b536bc0` can resolve an existing component face, reconstruct a wrapper and clear caches. It can set the original reference's `f60` to 2, or to 1 when the reconstructed reference has `f64==0` (`0x4b536e26..e4f`). The caller can replace the existing row pointer at `0x4b52b528..562` while keeping its allocated ID word. A constructor-only list of defaults cannot stand in for that path.

The simple retained-pointer case requires neither original nor swapped key to find earlier state, with no special `model+0x1350` path superseding it. Root's independent owner/hash work must supply that predicate.

The later `0x4b5360d0` pass checks actual virtual `+0xf8`. The actual FaceRef table resolves that slot to the zero-return leaf, so the pass skips this class. This closes one apparent late mutation route; it does not eliminate the validator above.

`tempEdgeHelper` also installs and releases temporary model surface maps and nested ID holders. Its destructor is not assumed to be collector-only. Complete nested representation lifetime effects are retained as a boundary. No live-row mutation is inferred from a container destructor name.

Under the ordinary store context, BEnt emits its retained scalar words at `0x4bba381f..3886` and its actual inline bodies. Face Serialize includes its empty match-array count when helper condition bit `0x80` is clear. The CompFace store emits the common CompRef body, alias presence, actual reference pointer and optional external pointer. CompRef's native `f84=0` and presence normalization remain distinct from raw wire retention. [Component wire](DownstreamComponentWire2026.md) and [entity-reference wire](DownstreamEntityReferenceWire2026.md)

## Bounded next construction and proof

A first model-derived face row can receive the actual post-context surface-owner nodes, actual loop/coedge order, actual component clone, actual body atom and actual counter state. It can compute six inline rows, the selected mode-0 scalars, an explicitly prefix-derived role map and the real pointer aliases. It must refuse or separately represent the unsupported mode, ambiguity, map and lifetime branches above.

This does not produce a complete downstream cache or establish that an emitted cache loads without warning32. The next root-owned proof is exact graph construction and archive readback, followed by a fresh controlled native load/rebuild/save comparison. This source tranche executed zero SDK or vendor processes and left every predecessor receipt unchanged.

Run [VerifyFreshFaceSources.py](../../tooling/sw2026/downstream/VerifyFreshFaceSources.py) with the licensed `--bin-directory`, this `--record` and an unused `--output`. It hashes original source intervals and vtable/descriptor cells only. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and full [RE playbook](../../Playbook/README.md) apply before further construction.
