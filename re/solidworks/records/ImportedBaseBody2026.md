# Native imported base-body ownership in SOLIDWORKS 2026

Task `B04-SW2026-IMPORTED-BODY` belongs to [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The task covers a native imported-body representation for neutral geometry
without a qualified editable feature mapping. Its dependencies include the
base feature grammar, owned kernel geometry, actual atom publication and
explicit capability-loss reporting. Exit requires model-only generation,
strict readback, cold native open, rebuild, save and fresh reopen against
the original held-out sources.

## Native source

The exact SOLIDWORKS 2026 SP05.2 oracle creates `Imported1` as a real
`BaseBody` feature, with native identity 26. Four fresh processes pass the
disclosed authoring and read-only reopen, including both pristine controls.
The box has one solid, six planar faces, twelve line edges and eight
vertices. The reopened volume is 6,669 mm³, surface area is 2,222 mm²,
and the centre of mass is `(7, -11, 10.5)` mm. The feature's persistent
reference resolves before rebuild, and its six faces all alias the same
actual solid and owning import feature.

The initial observer rejected the source on the API type string after a
successful rebuild. It expected `Imported`. The corrected exact-build
observer checks `BaseBody` and the real persistent ownership.
[Initial type receipt](../measurements/2026/ImportedBodyInitialType01.json)

The sealed cohort passes six more fresh processes with both pristine
controls. Two independent native originals are locked by SHA-256 before
writer derivation. The [source-lock receipt](../measurements/2026/ImportedBaseBodySourcesNative01.json)
contains the opaque source hashes and the disclosed measurements. The
sealed source bytes, actual dimensions and logs remain in the guest.

## Archive frontier

The 49,188-byte disclosed source has SHA-256
`13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325`.
Its public SDK read recovers one boundary with the six faces, twelve
edges and eight vertices, as well as the `Imported1` history row. The
typed linked read stops at `moBaseBody_c` schema 1. The legacy read reports
the typed refusal and a separate property-manager ownership diagnostic.
The class spelling appears at byte 5,725 of the 6,080-byte
ResolvedFeatures stream. The disclosed Config-0 stream is 25,190 bytes
and its partition stream is 604 bytes.

The [2026 serialization map](../../data/Serialization/SerializeMap2026.json)
binds `moBaseBody_c` to `sldmopartu.dll` preferred address `0x1802fcb70`.
The exact x64 DLL SHA-256 is
`aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9`.
The image's PE runtime-function table gives the half-open wrapper interval
`[0x1802fcb70, 0x1802fcdd5)` and shared serializer interval
`[0x1802fd060, 0x1802fdcfc)`.
REA observes a direct call to the shared import serializer at
`0x1802fd060`. It also resolves alternate body-loading calls and an
older `moBodyFeature_c` serializer branch. The wrapper remains the first
required typed archive owner even though the import implementation is
shared. REA evidence ID
`ev_5bfac51b1afa7383f956ee35b1b5ad357f846c0051adfc3f6a81db52fa206dd0`
identifies the exact-image analysis. The linked body, marks and
partition publication still need correlation with the disclosed native save.

## Schema 1 witness replay

The measured class uses the shared `moBodyFeature_c` trunk. The primary
vtable at `0x180492e28` binds `SerializeLWData` through slot `0x4b8`,
`SerializeResolvedData` through `0x4c0`, the node's XML ID extraction
through `0x3f8`, and `SerializeXmlData` through `0x3e8`. In the exact
`sldmodu.dll` image (SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`),
the imported `moNode_c::getIdForXmlDataExtracter` at `0x4c03e170` publishes
the actual node key and returns true.

The disclosed part uses model version 19000 and all three archive
context flags set to one (`model_is_part`, `model_compressed_stream`
and `cmgr_f658`). The base consumes 305 bytes and advances the inherited
object map from 178 to 180. Its position in this file is 5,737 through
6,041 inclusive. The subclass then consumes a 34-byte suffix consisting
of CString, signed i32, CString and signed i32, in that order. The
observations are the empty string, 1, `Imported1` and 0. The four-byte
resolved trailer belongs to the shared stream framing.

Two independent runs of the
[witness codec](../../tooling/sw2026/imported_body_source/ReplayImportedBaseBody.py)
re-emit all bytes of Config-0, ResolvedFeatures, CMgr, ModelHeader and
Header2 from typed objects. The final Config-0 and ResolvedFeatures map
counts are 107 and 180. The codec requires the exact disclosed source
hash and the measured context. The
[replay receipt](../measurements/2026/ImportedBaseBodyWitnessReplay01.json)
records hashes and lengths for all five streams. Source classification
for the four subclass fields, populated kernel attachment and the
other version and mode branches remain open.

The source protocol writes vendor-authored control and source files.
The Kit writer, generated native fallback and public capability-loss
report remain open.
