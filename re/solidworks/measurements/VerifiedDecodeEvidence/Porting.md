<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Porting the verified SOLIDWORKS decodes

This evidence records an offline reader and editable FreeCAD output tested in a
working snapshot. The evidence commits do not install that reader or writer in
upstream Kit. They do not establish general SOLIDWORKS support or a lossless
round trip.

## Git basis

The original download identifies commit
`af3ae081e74b077f8686fbf6273a74d9a211b89e`. All 4,495 archived `src/` files
matched that Git tree byte for byte. The commit is an ancestor of the reviewed
`TryUniCAD/Kit` main at `1087ffe828caf3ef32b31f242ed3ebd69de30821`.

The research working snapshot added 1,711 source files and modified 11 against
that archive, with no deletions. All 11 modified paths also diverged upstream.
The research implementations of `core/Native.py` and `core/Adapter.py` still
import 28 files retired upstream, including recorded-family programs. Keep the
recorded-payload writer removal at `36d0136a7f0349c9f34e78d220ef0d02ee53fa78`.
Port the reader at the current entry points; copying either old module wholesale
would undo upstream work.

## Reader and writer boundaries

1. **Select the native configuration.** `OpenDocument` enters the SOLIDWORKS
   adapter through `core/Adapter.py::NativePartModel`. Reconcile the selected lane
   with `swXmlContents/KeyWords`, and pass the matching `Config-N`, `Config-N-ModelHeader`
   and `Config-N-ResolvedFeatures` buffers to the typed reader. The executed
   path must use the actual native resolved lane. Upstream `ResolvedStream` can
   prefer the kit lane, which is not evidence for the original native tree.
2. **Replay the saved namespace.** Qualify Config once and retain its record,
   class/object maps, schemas and allocation counter. Use that state to parse
   the resolved roots, owned children and list return. Adapt group calls to
   the current `container/Archive.py` and `container/RunGroups.py` contracts.
   Compare reconstructed bytes and final reference maps in tests. Constants
   should describe types and field grammar, never particular file offsets,
   reference indices or saved payloads.
3. **Bind before rebinding.** Upstream `core/Native.py::DecodeNative` calls
   `ParseKeywords` before `RebindIds`. Reconcile raw keyword IDs and scalar
   values with the typed binary tree at that boundary, then project the actual
   support plane, directed sketch entities, constraints, profile and parameter
   owners. A recognized but malformed family must fail explicitly. Do not
   fall back to cached marker geometry, keyword dimensions or guessed owners.
4. **Emit from the neutral model.** Use `WriteDocument` and the current FreeCAD
   `CanWriteFeature` and `Archive.py` emitters, composed by
   `ArchiveOutput/ArchiveWrite.py`. Preserve independently editable drivers,
   feature and sketch links, and exact placement. Derive a fillet selector
   from the connected target wire rather than source entity order. Rebuild
   any native selection payload from semantic fields. Do not copy a vendor
   archive entry, recorded SolidWorks program or cached B-rep into the edit
   path as a substitute for an executable feature.

## What was exercised

The offline path read the native files, recovered typed ownership and emitted
FreeCAD archives plus standalone Python. The accepted runs regenerated the
archives after access to the original vendor inputs was revoked. Separate
SOLIDWORKS and FreeCAD sessions were used for validation only. The application
checks measured a live feature tree, one valid solid, placement, volume and
centre of mass, plus driver edits, rebuilds and restoration. These results
cover the recorded families and cases on the research implementation; upstream
integration must recheck the new reader and writer boundaries.

For parameterized offset starts, the source proof separately binds the blind
`EndSpec` depth and the raw-type-5 `FromEndSpec` offset display, and confirms
that the offset flip is independent of depth reversal. Three read-only source
checks confirmed healthy rebuilds, one solid, and the actual depth and offset
values. This establishes source semantics, not application acceptance of a
production offset-start port. Verify the target's live offset and blind depth
independently before reporting that port usable.
