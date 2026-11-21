# Standalone downstream archive maps in SOLIDWORKS 2026

**Ordinary standalone reader map initialization is statically closed.** Both supported concrete storage routes construct a fresh archive and initialize one null-reserved class/object namespace. Actual saved-stream replay, reached class closure and the top-level standalone save invocation remain unqualified.

| Item | Scope |
| --- | --- |
| Task | B04-SW2026-DOWNSTREAM-ID-DATA, standalone I/O dependency |
| Owner | `/root/flag_ownership` for source evidence, root for codec integration and the native oracle |
| Delivery | PR #121 |
| Profile | Ordinary version 19000, non-DB read, current configuration, structured or zip storage, raw or compressed stream |
| Inputs | Original licensed release DLLs and current shared SDK source |
| Exit | Apply this namespace rule to a complete typed body codec, then bind an actual disclosed standalone stream and every reached class/context before admission |

This record closes the selected read-side map-origin question for the existing body grammar. [Body grammar](DownstreamIdArchiveGrammar2026.md)

## Concrete storage dispatch

The [numeric proof](DownstreamStandaloneMaps2026.json) binds 25 complete native owners, 20 instruction windows, three actual RTTI/table identities and fourteen source-only SDK fingerprints. All native hashes use unchanged original bytes, declared PE exception-directory sizes and complete chained extents. No native listings are included.

| Module | SHA-256 | Preferred base |
| --- | --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` | `0x3c720000` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` | `0x31a30000` |

The ordinary loader `0x4b5860e0` obtains `suFileStorage::getSharedStorage`, attaches `Contents` with `(mode=0,isStream=0)`, and attaches the actual configuration storage name plus `-DownstreamIdData` with `(mode=0,isStream=1)`. Reading an existing stream dispatches by its actual storage-node kind when the fifth compression argument is zero.

The relevant actual primary tables are:

| Concrete RTTI class | Table | Slot `+0xa0` |
| --- | --- | --- |
| `suStructuredStorage` | `0x3cc7e8f0` | `attachToNode` at `0x3c8b3fe0` |
| `suZipStorage` | `0x3cc7e680` | `attachToNode` at `0x3c8b4140` |
| Base `suFileStorage` | `0x3cc7e418` | `0x3c7509d0` (base implementation) |

Constructor instructions install these actual tables. The shared-storage path can construct the zip wrapper directly. The path factory selects the corresponding concrete storage otherwise.

Every successful selected read stream reaches a fresh archive allocation:

| Storage/path | Complete read helper | Archive constructor call |
| --- | --- | --- |
| Structured, raw | `[0x3c8b7c70,0x3c8b7e80)` | `0x3c8b7e11` |
| Zip, raw | `[0x3c8b7e80,0x3c8b80eb)` | `0x3c8b80a0` |
| Structured, compressed | `[0x3c8b8180,0x3c8b8334)` | `0x3c8b82b4` |
| Zip, compressed | `[0x3c8b8340,0x3c8b850f)` | `0x3c8b84a9` |

Each call resolves through `sldmfcu` IAT `0x3cb1d588` to `swccu!su_CArchive(CFile*,unsigned,int,void*)` at `0x31a33100`. It receives mode 3 and a new archive object, then installs that actual object into storage `+0x18`. The selected read paths clear archive `+0x08` to zero and carry the actual storage context in archive `+0x00`. There is no copy of Header, Config, Resolved, object-map or schema-map state.

The outer loader retrieves this archive, constructs its helper with condition word zero, actual model and null context/history, installs the effective file version, sets `SerializingDownstreamIdData`, and calls the direct downstream Serialize slot at `0x4b58630f`. No downstream root class/object slot or Header direct alias is bound. No map-count word is consumed before the body. The adjacent helper `[0x4b5863c0,0x4b5865c3)` is another explicit-configuration **read** route with the same fresh framing, not a save witness.

## Lazy native initialization

Complete archive constructor `[0x31a33100,0x31a33263)` has SHA-256 `fda9938ef7b81a5249bb9fea48a98bd608dc0fd19632338cc54713191b611e19`. It initially writes counter `+0x50=0`, pointer/load-array member `+0x58=NULL` and schema-map member `+0x60=NULL`. A constructor's uninitialized map is distinct from the logical namespace used by the first object tag.

`MapObject(NULL)` at `[0x31a3a110,0x31a3a2c9)` initializes the map lazily:

- Load: allocate a one-element load array, put null at index zero, set next counter one.
- Store: allocate a pointer map, associate the null key with index zero, set next counter one.

`ReadClass` calls it at `0x31a3a309`, before reading the u16 tag at `0x31a3a316`. `WriteObject` calls it at `0x31a3a954`, before its null/non-null branch. Thus a null pointer operation also initializes the reserved null slot. Null does not allocate a positive entry. The ordinary storage mode 3 has archive flag `0x10` clear, so `ReadObject` does not take that flag's no-input null return.

Classes and objects share the initialized counter. A first nonnull new-class object gets class index one, then object index two, with next counter three before its body. A later object of that class allocates only an object entry. Nulls and existing references allocate zero entries. Native read registers the object before invoking its body, preserving cycles. The existing tag rule supplies width selection, membership checks, schema policy and the allocation limit. [Tag grammar](ArchiveTagGrammar2026.md)

If no pointer operation is reached, the native lazy map can remain uninitialized with physical counter zero. There is no serialized map-count prefix to change from zero to one. Do not emit either number as extra bytes.

## Shared SDK boundary

The existing SDK components fit this initialized namespace without another object representation:

| Shared source | Correct reuse |
| --- | --- |
| `ArchiveMaps(1)` with no snapshot seed | Logical null-reserved namespace, initially no positive class/object entries |
| `ReadTypeMut` / `WriteClassMut` | New class registration from the same shared counter |
| `ReadObjectMut` / `WriteObjectMut` | Actual object registration before body recursion and identity-based reuse |
| `ReadBodyMut` / `WriteBodyMut` | Direct body framing once that exact class/layout/context is admitted |
| `ArchiveNode`, typed callbacks and generic tag/scalar/string primitives | Existing typed graph and wire operations |

Invoke the standalone root body directly with `ArchiveMaps(1)` to preserve its logical class/object indices. The native constructor retains a physical counter of zero until the first pointer operation.

The SDK comparison is source inspection only. Its current field-admission guards still apply, including unsupported concrete classes and special helper contexts. Several reachable pointer-family bodies remain outside full current downstream closure. No SDK source, body schema or test was executed by this tranche.

## Kept limits and next evidence

This closes selected standalone **read** archive creation and the initial logical seed. Common storage write branches construct fresh mode-2 archives with the proven generic store-map allocation rule. The top-level standalone model-save invocation remains open. The identified `createOrUpdateDownstreamIdData` method edits runtime data.

A dedicated disclosed saved downstream stream is still needed for whole-body cursor, exact bytes, map/alias parity and every reached concrete schema/context. There is no native application run, live trace, vendor load/rebuild acceptance or held-out generalization. DB, add-configuration and other storage modes remain outside this selected rule.

The governing stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This static dependency handoff does not mark the CAD goal complete.

[Lazy-map gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/ArchiveMapsInitializeLazily.md) · [Change](../../../Documentation/Changes/Solidworks/Inspection/Downstream/SolidworksStandaloneDownstreamMaps.md)
