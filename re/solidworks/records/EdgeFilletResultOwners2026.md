# Fresh result owners for the ordinary edge fillet

Task `B04-SW2026-EDGE-FILLET-SOURCES` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
This static result uses exact SOLIDWORKS 2026 SP05.2 AMD64 images and the
four [disclosed original and edited fillet saves](EdgeFilletArchive2026.md).
The [source-span receipt](../measurements/2026/EdgeFilletResultOwnersStatic01.json)
pins the executable build `34.5.2.0604`, all four module digests, 31 original
PE spans with byte hashes, and the exact Fillet virtual dispatch cells.
Hopper through REA identified the part module procedures. Apple LLVM 21
independently decoded the unchanged original PE bytes. Native execution
and a new fillet output are outside this result.

## Initial allocations and wire counts

`sldmopartu!0x180605a60` identifies the actual `Fillet_c` archive class
and its `0xc50`-byte factory at `0x180268d30`. The factory invokes the
default constructor `0x1802699e0`. That constructor initializes `this+0x9b8`
and `this+0xbf0` with the default `suPtrMap` at `0x180269a6b` and
`0x180269b26`. The authored-feature constructor `0x180269d00` does the same
at `0x180269daf` and `0x180269e69`. Both instantiate the edge keeper with
the actual Fillet as its body-feature owner.

The imported `sldmfcu!0x3c7a9080` default map constructor passes block
size ten to `swccu!0x31a49c30`. That base constructor's qword write at
`0x31a49c5a` sets capacity at `+0x10` to 17 and the actual signed count
at `+0x14` to zero. The bucket pointer is null. Capacity and block size
are allocator state. The serializer writes the count from `Fillet+0x9cc`
or `Fillet+0xc04` at `0x1802706af` and `0x1802709bf`, respectively.
For the current version, the present `f9b8` lane remains within the
`has_f734` section. Both read loops skip rows at count zero
(`0x18027193a` and `0x180271ba1`). The initial emitted value for either
present map is a signed count of zero and no row bytes.

The `moFilletSIdKeeper_c` constructor `sldmodu!0x4c6d6090` gives the base
`f18` array a null data pointer via `0x4c6d61d0`. The persistent `ff0`
array at `+0xf0` and its pending peer at `+0x110` have separate
`su_CObArray` constructors. `swccu!0x31a3cb97` initializes each count to
zero. The edge keeper retains its actual body-feature pointer at `+0x130`.
The current keeper serializer `0x4bba9860` visits `f18` first and then
`ff0`. The `f18` signed count read at `0x4bbaab97` skips its row loop at
zero. The empty `ff0` also skips the post-read retained-reference loop at
`0x4bba98bd`. A fresh edge keeper therefore has two present empty
collections in their existing grammars. [Keeper initialization gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/Fillets/FreshFilletKeepersStartEmpty.md)

## Where the current solve fills those collections

The exact ordinary solve begins at `sldmopartu!0x1802a6cc0`. Its kernel
call to `ramFilletEdge` is at `0x1802a88dd`. The following observations
trace native state for the bounded single convex edge case.

### Corner data `fbf0`

Environment query `0x4f3` and a nonnull actual body gate the pre-solve
call `0x1802a7fae` to `setupEdgeDataForCorners` (`0x1802b8920`). It
collects live edges with mode 1 and the comparison collection with mode
0, calls `getFirstRadius`, and clears the previous map at `0x1802b89df`.
The clear path explicitly skips its rows when count is zero
(`0x1802ae495`) and invokes `RemoveAll` at `0x1802ae7d7`.
Each new row gets its own `moCompEdge_c` around the live selected stock
edge and actual self component. The fields written immediately before
insertion at `0x1802b8ae9` have these source rules:

| Row field | Native source |
| --- | --- |
| `f00` | 1 only when the physical `this+0x81c` policy is nonzero and the edge is absent from the mode-0 live collection. The other branch emits 0. |
| `f04` | The actual `gcEdge_w::isConvexEdge` result. |
| `f08` | The first actual fillet radius from `getFirstRadius`. |
| `edge` | A new `moCompEdge_c` constructed from the live stock edge with the actual model's self component. |

The separate corner-data reader at `0x18027f038` returns no result for
an empty map. Warm storage contains one row on each of the four saves,
with policy `f81c = 0`, convex result 1 and radius equal to the real D1.
The native row is therefore supported as recomputed **before** the kernel
operation on its enabled branch. The environment query's policy remains
a gate, and the analysis does not assign that setting to other modes.

### Edge keeper `f820`

Before edge collection, `0x1802a6d55` invokes `sldmodu!0x4c6d8100`
with the actual stock and SID cache. `reset` reaches the generic surface
constructor at `0x4c6d832e` when `f18` is empty. It appends that ID as
the first row at `0x4c6d8431`, using the actual body-feature pointer at
`+0x130`. It begins prior-result traversal at index 1 and checks the
current surface count at `0x4c6d84d1`. Existing edge references are used
only after the saved ordinal is bounded by the actual `ff0` count
at `0x4c6d8586`.

The selected-edge collector calls `set` at `0x1802ac7a2`. For the
non-patterned case, `sldmodu!0x4c6d8a2e` retains the actual selected
reference in the **pending** array `+0x110` and indexes it by the live
edge in the separate `+0xb0` map. The persistent `ff0` is still empty on
that fresh path. Following a successful kernel return, status at
`0x1802a8c9e` gates the actual Fillet `iAssignFaceIds` vtable call at
`0x1802a8e13`. This dispatch resolves to `0x180289be0`. Its ordinary
edge-mode helper `0x18029c620` calls `createFilletId` at `0x18029c82e`
for the pending live edge. `sldmodu!0x4c6d6e02` moves the held reference
to `ff0` with its original identity. The previous `ff0` count plus one
feeds `makeFilletSurfaceId` at `0x4c6d6e23`, together with the real
feature owner. `0x4c6d6e31` appends that produced ID to `f18`.

The saved generic and produced surface rows plus the `ff0` alias agree
with that lifecycle. The generic-only intermediate is an in-memory
state on this path. Existing saved-reader cardinality stays unchanged.

### Result face associations `f9b8`

The association lookup at `0x1802893af` returns false at count zero.
After the successful kernel operation and output identification,
`0x1802a99ae` calls `0x180290090`. This helper builds transient
`f988` associations from actual solved faces and linked edge data. One
insertion is `0x1802901f2` with the face key from the live result list.
The native completion callback at `sldmodu!0x4b71ab00` uses Fillet's
vtable slot `+0x23b8`, validated from its actual constructor-installed
vtable. This call is gated by the `0x4f3` setting, the concrete Fillet
flag at `+0x808`, and the `+0x8dc == 1` edge mode. All four disclosed
saves have wire `f8dc = 1`.

The callback `sldmopartu!0x1802b82d0` frees prior entries, clears the
actual `f9b8` map at `0x1802b8315`, and walks its `f988` live face-edge
associations. It constructs a component face from each real result face
and the actual self component at `0x1802b83b5`, obtains the associated
edge through the stored object's virtual slot `+0x108`, and inserts the
pair at `0x1802b83db`. The positive saved result-face handle belongs to
that derived result and is not an initial stock handle.

## Scope of the rules

The initial zero rows follow the actual native constructors and read
framing. The live paths above explain the saved rows without replaying
their values. This is sufficient evidence for the four initial
collections in a private model-generated candidate. The full cold-file
load, the remaining live stock-reference and selection direction rules,
the independent `fc20` closure, and successful empty-to-populated save
and reopen still have separate qualification gates. No native acceptance
or held-out credit is recorded here. [Construction boundary](EdgeFilletConstructionBoundary2026.md)

Recompute original file offsets and hashes with `MaterialPe.PeImage.pin`
from [the existing PE helper](../../tooling/sw2026/materials/MaterialPe.py)
and the explicit half-open spans in the receipt. Keep all images and
disassembly output outside Kit. The receipt retains addresses, identities
and digests only.
