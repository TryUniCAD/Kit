# Sketch and profile tag field semantics

The two previously unnamed `profile_edge_tag_data` sets are **start-adjacent primary sketch tag IDs** at object offset `0x20` and **end-adjacent primary sketch tag IDs** at `0x38`. This is established by the constructing code, not inferred only from the serializer's `SA` and `EA` labels.

The [machine-readable evidence](SketchTagSemantics.json) binds the addresses to the installed binary hashes. Addresses are unslid ARM64 virtual addresses from Fusion build 2706.1. Inspection used `nm -arch arm64`, `c++filt`, and `otool -arch arm64 -tvV`. It did not call Fusion or execute tests.

## Endpoint adjacency construction

`NaTagUtility10` exports the local symbols `TaggingInterface::SketchTagUtility::getSketchProfileTagData(EDGE*)` at `0x2e5bc` and `getPrimaryIdsFromEdgeSet` at `0x2e4b0`.

The first function collects edges through `Ns::ASMInterface::adjacentEdgeOnStartV` at `0x2e614`, then `adjacentEdgeOnEndV` at `0x2e620`. It converts each edge set using `getPrimaryIdsFromEdgeSet`; that helper reads `sketch_tag_id+0x8` at `0x2e504`, then inserts the value into a `std::set<unsigned long long>` at `0x2e518`. It therefore preserves primary curve tags only, rather than entire sketch tag tuples or entity pointers.

The start set is passed in `x2` and end set in `x3` to the three-argument `profile_edge_tag_data` constructor at `0x2e64c`. `NsASMInterface10` constructor `0xde988` saves those arguments in `x22`/`x21`, then copies them to object offsets `0x20`/`0x38` at `0xde9d8` and `0xde9e4` respectively. A separate `ProgenitorDataCreator::create_progenitor_data` path performs the same conversion at `0x29d00–0x29e74`.

The binary callback layout remains version, counted sketch-tag vector, counted start-adjacent primary-ID set, counted end-adjacent primary-ID set. Each set contains uint64 IDs in ascending unique order. The native matching implementation also compares endpoint sets in reversed orientation; swapping start and end does not make them arbitrary unordered collections of collections.

## Sketch discriminator at offset 0x20

The `sketch_tag_id` uint64 at object offset `0x20` is still not assigned a definitive native member name. Its exact width, version gate, and equality role are known. It is zero-initialized, introduced at serialized version 2, and participates in `match`/`exactMatch` independently of the primary and secondary identifiers.

A nonzero producer proves it cannot be treated as universally unused or casually renamed as another curve ID. In `NaFusion10`, `(anonymous namespace)::tag_corner_relief` at `0xcdff20` constructs a tag with primary ID `3000` or `3001` selected by its first boolean argument, then ORs `0x04000a20` into the offset-`0x20` uint64 at `0xcdff5c–0xcdff6c`. It attaches that tag through `createSketchAttribDef` at `0xcdff78`. This establishes bitwise discriminator/flag composition in at least the sheet-metal corner-relief path. The complete allocation of those bits and the original member name remain unresolved.

Binary streaming and string serialization use different field orders: the binary callback writes this field after split sequence and total, whereas `saveToString` writes it after direction and before the split fields. Reusing one ordering for the other corrupts semantic values.

`compareDirection` at `0xdc8bc` also recognizes uint32 `0xffffffff` as a wildcard. This observation concerns the native object's matcher; it does not independently prove that every persistence callback retains that sentinel rather than normalizing its representation.

## Additional role-flag producers

`NaSheetmetal10` supplies several independent constructors and tag-copy paths. They establish the behavioral description **topology role flags** for the uint64, without recovering the original member spelling or every bit's enum name.

| Named operation | ARM64 write range | Mask composed with existing flags |
| --- | --- | --- |
| `NaMiteredFlange::tag_unfolded_edge` | `0x14d34–0x14d6c` | `0x04000022` or `0x04000042`, plus optional `0x04000400` |
| `NaMiteredFlange::transfer_tag_attribute` | `0x14e28–0x14e38` | Optional `0x04000400` |
| `NaMiteredFlange::transfer_tag_attribute_bend_relief` | `0x14ed8–0x14ef0` | `0x20` or `0x40` |
| `NaMiteredFlange::tag_corner_relief` | `0x14f8c–0x14fc4` | `0x04000800`, side choice `0x20`/`0x40`, optional `0x04000200` |
| `NaTagMgrFlangeProfile::tag_planar_wire_fillet` | `0x31d58–0x31d68` | `0x04000200` |
| `NaTagMgrFlangeProfile::makeTag` | `0x3021c–0x30230` | Optional `0x04000200` |

These are masks associated with the named operations, not a claimed complete enum. In particular, the Boolean arguments' original parameter names are absent from symbols, so the `0x20`/`0x40` distinction must not be labeled left/right or start/end without further evidence.

The [read-only corpus sampler](SketchTagSamples.py) examined all 712 archives and found [5,077 decoded callback values](SketchTagSamples.json), all with zero role flags, with no unresolved records or archive failures. This corpus establishes the prevalence of zero in those files; it does not establish that nonzero flags are invalid. The static producer paths prove otherwise.
