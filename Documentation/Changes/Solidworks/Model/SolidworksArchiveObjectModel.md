# SOLIDWORKS archive object and map model

The production archive layer now has typed nodes, class descriptors, external references, shared counters, map snapshots, and callback-driven class/object operations under `Archive/Objects/` and `Archive/Maps/`. It computes bookkeeping from the current in-memory graph. It supplies no feature fields or saved defaults and reads no files, research data, native library, or CAD application.

## Values and map ownership

`RuntimeClass(NameValue, SchemaValue)` carries the archive's class name and unsigned-u16 wire schema. It is an immutable descriptor, not a native runtime pointer or versionability flag. Descriptor encoding, name limits, registry admission, and expected native ancestry belong to the supplied descriptor and body callbacks.

`ExternalClass(NameValue, IndexValue)` identifies an explicitly bound inherited class whose descriptor was not present in the current stream. It has no schema value. `ExternalRef(IndexValue)` identifies a missing inherited object slot. Neither type supplies a feature default or infers a concrete class from a feature name.

`ArchiveNode(ClassValue, FieldsValue)` holds a `RuntimeClass` or `ExternalClass` and a caller-owned `MutableMapping[str, object]`. The mapping is retained directly, so computed field providers stay lazy. Equality remains based on object identity. `StartOffset`, `EndOffset`, and `IndexValue` are optional local provenance, initialized to `None`; stores do not use them to emit indices or patch output. A subclass factory may provide research compatibility properties without changing the production model.

`MapEntry(IndexValue, EntryValue)` distinguishes descriptor and object owners. `MapSnapshot(CounterValue, EntriesValue)` freezes the counter and tuple of typed entries, rejecting null/reserved indices, duplicate slots, and slots at or beyond the next counter. `ArchiveMaps(BaseValue, SeedValue=None)` validates the stream base against its seed and copies map membership. `Snapshot()` retains complete membership and strong node references, preserving identity across configuration and resolved streams. It does not deep-copy field payloads or freeze model edits.

The native allocation guard requires the next index to be less than `0x3ffffffe`; a completed map counter can equal that boundary. Reference tags retain their separate unsigned-31-bit domain. Sparse inherited maps are supported. When aliases occupy distinct slots, snapshots retain every slot; inverse class/object lookup follows the last entry in seed order, matching the existing Core seed behavior.

## Class and object operations

The focused map functions are `FindClass`, `FindObject`, `ClassIndex`, `ObjectIndex`, `AddEntryMut`, `BindClassMut`, and `PutEntryMut`. The latter is the internal typed slot insertion boundary used by allocation, seeding, and explicit inherited binding. `BindClassMut` fills only a missing prefix slot and never advances the counter. Conflicting bindings fail. Seed complete maps when their configuration context is available.

`ObjectRead` requires a map and five explicit callbacks: `TagReader`, `ClassReader`, `BodyReader`, `NodeFactory`, and `ReadOffset`. `ReadClassMut(ReaderValue)` accepts null, new-class, or class-reference tags. `ReadObjectMut(ReaderValue)` additionally resolves object references, creates a node for a class tag, registers it before reading its body, and records its stream-local provenance. `ReadTypeMut` owns class declaration/reference resolution.

`ObjectStore` requires a map and `TagWriter`, `ClassWriter`, and `BodyWriter` callbacks. `WriteClassMut(WriterValue, ClassValue)` emits a null, inherited class reference, existing class reference, or new descriptor. `WriteObjectMut(WriterValue, NodeValue)` reuses mapped identities or registers a new object before its body callback. This ordering preserves cycles and shared references. Equal field values do not merge distinct objects.

Descriptor callbacks own the separate class descriptor grammar; they must not substitute ordinary CString encoding. Tag callbacks use the shared tag primitives. Primitive count/string calls and feature registry operations remain in their actual owners. No optional empty body callback or unknown-class fallback exists.

## Errors and boundaries

Invalid value types raise `TypeError`; invalid domains, seed mismatches, conflicting slots, wrong-kind references, and dangling local references raise `ValueError`. Only a missing positive object slot below the stream base becomes `ExternalRef`. Missing class references require explicit prefix binding. Stores reject external object indices outside the inherited prefix and references to known class slots.

Callback exceptions propagate. As with the existing Core, callers must discard an unsuccessful stream and its partially advanced state; this layer does not roll back consumed/emitted bytes or failed body mutations. Callback implementations must enforce their own version, archive-mode, schema, and field admission. Runtime proxy repair and native ancestry/schema-version normalization are not invented by this model.

The [lazy mapping gotcha](../../../Gotchas/Conversion/Solidworks/Archive/LazyFieldsRetainMappingOwnership.md) explains why payload materialization changes construction behavior. The [native map record](../../../../re/solidworks/records/ArchiveMapConstruction2026.md) and [tag grammar](../../../../re/solidworks/records/ArchiveTagGrammar2026.md) bind the counter, null/reference grammar, and linked-map ownership rules.

## Verification

The research `Obj` is a compatibility subclass of `ArchiveNode`.
Its field mapping and provenance retain the existing research interface.
Actual class/object reads and writes use the production controllers and the existing registry callbacks.
`MapBridge.py` converts explicit legacy descriptors and map views without importing research code into production.
Inherited class bindings use `BindClassMut` instead of mutating a parallel table.
Configuration direct bindings update the store's inherited-prefix boundary as the load path already did.
This boundary validates external references without supplying missing model values.

Field inventories fingerprint every map/object package module and the bridge.
Their real CLI process assertions require that exact implementation inventory.
Static source, AST, and formatting checks passed without executing a codec, schema, or local test.
Every production declaration is below the live 30-logical-line limit.
The first remote integration run preserved archive bytes but failed the linked field-inventory identity assertion.
The [map-view gotcha](../../../Gotchas/Conversion/Solidworks/Archive/LinkedMapViewsRetainEntryIdentity.md) records the compatibility-row identity error and its correction.
Resolved streams now inherit the typed snapshot directly.
Their compatibility views retain each immutable entry's identity through a shared, scoped memo.
The original linked assertion remains active.
All current PR CI passed on source `9d7209d515d6d7c6fafa461ae7dad917c97f8226`, including the original linked identity assertion.
The [source-admission receipt](../../../../re/solidworks/measurements/2026/CurveArchiveModelAdmission9d7209.json) binds 234 strict byte identities, 234 retained field graphs, 83 matching implementation fingerprints, and 99,579 node occurrences to that tested revision.
The configured automated review reports failed to finish and no current-head approval is available.

The production adapter remains read-only. This shared infrastructure supplies no fresh feature builder and establishes no held-out native output acceptance, rebuild result, or complete CAD conversion coverage.
