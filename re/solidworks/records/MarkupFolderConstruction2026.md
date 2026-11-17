# 2026 markup folder construction and class distinction

## Scope and identity

These facts apply to SOLIDWORKS `34.5.2.0604`, model module `sldmodu.dll`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
preferred image base `0x4b140000`. The module hash was recomputed. Original PE
exports, vtable pointers, runtime-function records and bounded LLVM instruction
reads corroborate the regenerated 2026 serializer map. No target code or CAD
parser executed. Vendor listings and binaries remain outside checkouts.

The [2026 map](../../data/Serialization/SerializeMap2026.json) identifies
`moInkMarkupFolder_c` primary vtable `0x4d072820` and inherited serializer
`moFolder_c::Serialize` at `0x4beb1bc0`. Direct original-byte reads confirm that
vtable slot `+0x28` points to that same serializer.

## Constructor and fields

The ordinary constructor is the complete half-open range
`[0x4beae190, 0x4beae1ce)`, 62 bytes, SHA-256
`b5bbdcd3a36eca32e31887c393a6760493ed7c1cb570da995df57c01ce298265`.
Its own unwind record has flags `2`; the inspected body ends in an explicit
return. It calls base folder constructor `0x4beae110`, installs the primary
vtable and secondary `0x4d074508` table at runtime `+0x90`, and writes integer
`1` to runtime `+0x360`. It adds no notes-area fields or caption-resource load.
The complete runtime-function table has no reverse-chained child ranges for
this constructor, its base constructor, the inherited serializer or the getter
below; the quoted extents do not omit split unwind fragments.

The base folder constructor clears runtime `+0x358`, sets `+0x360=1`, sets the
`+0x364` qword to one, clears `+0x36c`, and passes its supplied owner to
`moFeature_c::setOwner`. In particular `+0x370=0` follows from that clear.
The independently authored folder factory already models those two serialized
values as `f360` and `f370`; admitting the concrete markup class must retain
those rules rather than borrowing a saved node.

The complete inherited serializer range `[0x4beb1bc0, 0x4beb1cb0)` is 240 bytes,
SHA-256 `a48f7a5511132c749ba759b780d35a4f5f09de69e3e1b58d613744338cc39fa9`.
Its store path calls the inherited feature serializer, then stores the two
32-bit fields at runtime `+0x360` and `+0x370`. The load path gates those fields
at versions `>=0x0a93` and `>=0x27b4` respectively. This is the existing
`moFolder_c` schema; there is no markup-specific serialization tail here.

## Lookup and cache distinction

The exported `getInkMarkupFolder` method is the complete range
`[0x4c021ea0, 0x4c021f01)`, 97 bytes, SHA-256
`5e07fc0d632b3b0759982f7516a9e694f8e767807fc359813ced32cd29f17b8a`.
It obtains the concrete class descriptor through `0x4beb1630`, dispatches through
owner vtable `+0xf78` with that descriptor and returns the first collection item,
or null for an empty result. Thus a same-named notes-area node does not satisfy
this concrete runtime-class search.

The separately exported `setInkMarkupFolder` is an eight-byte leaf at
`[0x4b292c60, 0x4b292c68)` that writes the supplied pointer to owner runtime
`+0x238`. This does not establish a serialized field at that offset, nor does
the observed getter read that slot. Do not invent a wire cache or an archive
patch from this runtime setter.

## Localized default vocabulary

Primary vtable `+0x1568` targets the six-byte leaf at `0x4beb6b00`, which returns
resource ID `0x7f6f`. The `+0x4a8` method at `0x4beb6660` also loads that ID and
assigns the resulting CString to its supplied output. The selected
[REA-backed resource receipt](../measurements/2026/MarkupResource01.json) resolves
language `1033` to `Markups` in `sldresu.dll`, whose full SHA-256 is
`531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111`.
The resource is block `2039`, entry `15`, at file offset `2965976`, length
`3432`, SHA-256 `466dbb6f564764768d36fd9b87e1d6af06d94e2ed5cc78b0b6238f869f55b1f7`.
All sixteen length-prefixed UTF-16 entries consume that block exactly. Only the
selected seven-character vocabulary and format locations/hashes are recorded.
No resource payload is redistributed. Runtime language fallback is not observed,
so this is not an English-default rule for every locale.

## Observed tree consequence and writer verification

The existing controlled recursive-tree receipt includes an extra top-level
`NotesAreaFtrFolder` node in generated parts, plus a distinct native
`InkMarkupFolder` node. The already-unsealed independent camera source API
observations have the ordinary markup node but no extra top-level notes area;
native annotation notes remain children of `Annotations`.

The concrete class distinction is confirmed. The exact native insertion caller
that produces the missing markup node was not traced here. Its observed later
tree position is not a general insertion-order formula.

The shared-model change admits the markup class and keeps notes-area ownership
separate, with counts and IDs recomputed from the graph. The
[independent source lock](../v2026/heldout/TreeSourceLock.json) precedes that
writer change. Both later [paired native measurements](../measurements/2026/TreeParityInspection01.json)
match the reference's 25-node tree through saves, driving edits and fresh
reopening. This is a bounded English part result, with no production coverage.

The [native Hopper query](../measurements/2026/MarkupHopperAnalysis01.json)
corroborates the base-constructor call and the three runtime assignments in the
original 62-byte constructor. Its saved analysis and decompiled result remain
outside the checkout. REA identified the original PE and reported the bridge
startup and saved-target limits; Hopper's native API supplied the successful
decompilation after reopening the completed database.
