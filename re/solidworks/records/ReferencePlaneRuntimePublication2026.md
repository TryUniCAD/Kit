# Reference-plane runtime-class publication

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. This exact-build static result corrects the typed source-audit preparation before any source model was decoded. It adds no writer and changes no shared serializer. Root owns the native oracle and shared registers.

## Concrete type and published type differ

The [managed construction path](ReferencePlaneManagedConstruction2026.md) really invokes the native `moConstraintDefaultPlaneRefplaneData_c` constructor. Its concrete RTTI name does **not** become its ordinary archive tag. Both that class and its base publish the same `CRuntimeClass` descriptor through virtual slot zero.

The model image is pinned `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, build `34.5.2.0604`. The [2026 serializer map](../../data/Serialization/SerializeMap2026.json) supplies RTTI/vtable labels, not an automatic proof that each label equals the published archive name.

| Native object | RTTI vtable | Slot-zero accessor | Published descriptor/name |
| --- | --- | --- | --- |
| `moConstraintDefaultPlaneRefplaneData_c` | `0x4ced2548` | `0x4b8df460` | `0x4dad2370`, `moConstraintRefplaneData_c` |
| `moConstraintRefplaneData_c` | `0x4cecfd60` | `0x4b8df460` | Same descriptor and name |
| `moRefPlaneDistanceGeom_c` | `0x4d173a70` | `0x4c2d89b0` | Its own `moRefPlaneDistanceGeom_c` name |

Both constrained-plane vtables also use serializer `0x4b8e2ac0`. Thus the constructor's concrete class and its class-map row remain useful native evidence, while the file decoder must register **`moConstraintRefplaneData_c`** for this ordinary published owner. This is a native class-publication rule, not an alias learned from a saved control.

The shared constrained-plane descriptor has native object size `0xe8`, raw schema word `0x80000001`, create-object function `0x4b8df400` and base-class accessor `0x4b8df3f0`. The raw schema word is native descriptor metadata; this record does not introduce a new physical stream field. The create-object body allocates `0xe8` bytes, initializes the common plane data, installs the base vtable and leaves interface `f88` null for subsequent load. The concrete default constructor at `0x4b8e0220` calls the three-geometry base constructor and then installs the default vtable; it does not replace the inherited slot-zero accessor.

## Actual archive call edge

Pinned `swccu.dll`, SHA-256 `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`, base `0x31a30000`, supplies the ordinary `su_CArchive` path. Its `WriteObject` calls the object's vtable slot zero at `0x31a3aa21`, passes that returned descriptor to `WriteClass` at `0x31a3aa29`, target `0x31a3a850`, and later invokes the framework serializer bridge at slot two. The [archive grammar record](ArchiveTagGrammar2026.md) binds the enclosing full function and tag/map rules.

Consequently, a serializer pointer shared by two RTTI classes does not establish two wire descriptors. Conversely, an object with the concrete default vtable still publishes the base descriptor in the proven ordinary object-store path. Other serialization modes and classes are not inferred from this one example.

## Reproduction

[ReferencePlaneRuntimeClass.py](../../tooling/sw2026/ReferencePlaneRuntimeClass.py) reads the exact original model/archive PEs and the existing serializer map. It follows the selected vtable slot-zero accessors, requires the pinned direct descriptor-return body, parses only their runtime descriptors, and verifies the original archive lookup/call window. It records names, sizes, flags, addresses and hashes; it emits no vendor code or listings and executes no target.

```sh
uv run --isolated --with pefile==2024.8.26 python -B \
  re/tooling/sw2026/ReferencePlaneRuntimeClass.py \
  /absolute/licensed/sldmodu.dll re/data/Serialization/SerializeMap2026.json \
  /absolute/unused/RuntimePublication.json \
  --archive-module /absolute/licensed/swccu.dll
```

The [receipt](../measurements/2026/ReferencePlaneRuntimeClassPublication01.json), SHA-256 `f6f86696597c39662674b7f5dfe95252c96c27f6b99a54a96cd42aa5619f24bb`, includes the original accessor/descriptor/factory extent identities and the archive dispatch-window hash. Default/base share the descriptor; distance geometry independently retains its own published name. Original PE instructions were separately checked with Apple LLVM. No native CAD source file, private specification or hidden observation was opened.

## Effect on the prepared audit

The first frozen source-audit snapshot (`ed6f338b…`) had provisionally treated the concrete default RTTI label as a wire name. It decoded no native source and is preserved as a superseded preparation. The corrected reader adds the published base owner and distance geometry only, with the same native field order and ordinary version-19000 guard. The [new source-audit binding](ReferencePlaneSourceCorrelation2026.md) targets freshly rooted source packet 03, whose author tools and neutral inputs are byte-identical to packet 02. No source-byte fitting or field-offset patch was made.

The [specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/RttiClassNamesCanDifferFromArchiveTags.md) records the distinction. Actual source correlation and generated native edit/save/reopen acceptance remain unfinished.

The later qualified `D01` save normalizes the single-reference API feature to the separately traced `moFaceRefPlnData_c` compatibility owner. It therefore does not exercise this constrained-base wire branch. The runtime publication rule remains exact static construction/store evidence; its source correlation is still pending for a source that retains the constrained owner.
