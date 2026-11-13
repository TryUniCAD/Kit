# SOLIDWORKS document-generation skew

## Expectation

Changing `_MO_VERSION_<n>` storage names should make a native 2026 stream readable, independently of the streams surrounding it.

## Actual behavior

The generation comes from the document context, not the individual stream name. A 2026 `ResolvedFeatures` stream read under a 2025 document hierarchy reaches the sketch's `sgBlockManager` five bytes early. Its block count is decoded as `0x805200`, `ReadObject(sgBlock)` returns null, and the next write through the null block crashes at `SLDMODU!0x4c3e2c0d`.

The same feature stream opens and rebuilds when the document uses compatible 2026 configuration records. The healthy trace has 730 object/class events; the incompatible trace stops after 435 and then raises the access violation.

The generation-sensitive records are not interchangeable versions of an opaque container. `Contents/Definition`, `Contents/CMgr`, and `Contents/Config-0` each have field-level changes. The gated legacy RV symbol fields are replaced by a typed 300-byte DSPBR body in the 2026 manager. The manager also adds a linked-null object reference and a variable-table presence flag.

## Workaround

Forward the document generation explicitly and emit a coherent record family for that generation. Do not mix a newly named `_MO_VERSION_19000` prefix with 2025 configuration bodies, and do not replace configuration bodies with donor streams.

The independent 2026 `CMgr` encoder in `src/convert/adapters/solidworks/container/Cmgr2026.py` retains the existing typed archive framing and field contracts. Its single-feature output rebuilt in SOLIDWORKS 34.5.2 with one body, 9,189 mm³, and an editable `D1@Boss-Extrude1`; a 17 mm unsaved live edit rebuilt to 17,357 mm³.

`Contents/Config-0` also shifts when its visual body grows. Once the 2026 visual replacement adds 196 bytes, additions must be anchored after that computed delta, not at the pre-growth offsets. For example, the plane-style record belongs at 2796, not 2600. Using the earlier offset splits the reference-plane record before its new tail and raises `AfxThrowFileException(1,-1,null)` (`genericException`, per Microsoft).

The paired independently generated 2026 `Config-0` closed that boundary. Fresh public writer outputs pass the same open, rebuild, body-count, geometry, feature-tree, and live-edit checks. The documented acceptance is limited to the five-line single-feature family; arbitrary SLDPRT histories, assemblies, and drawings require their own recovered generation families.

See [the five-line record](../../re/solidworks/records/PolylineFivePad.md).
