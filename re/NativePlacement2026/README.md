# Decimal native placement campaign

This is research evidence for Fusion and SOLIDWORKS readers. It does not qualify native writing, complete feature semantics or editable conversion.

The decoder source is main `f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2`. Task `A08h-Placement20261123` is owned by Codex. The campaign used the existing deterministic controller/supervisor, capacity one per application, one offline reader pool, Python 3.14 and no model advice or partial fallback.

## Scope and retained failures

All 303 planned jobs reached an outcome: 48 native batches and 255 committed-file replays. Capture is incomplete: 47 native batches returned all three files; one SOLIDWORKS batch failed through COM/RPC. The package retains 141 files from complete batches, two unqualified saved files from that failed batch, and the explicit missing after-control. The six hidden-window canary files are additional controls, outside those totals.

Each batch creates an ordinary rectangular boss with controls before and after its variation. Three principal planes, both extrusion directions and decimal width, height and depth vary. Twelve preselected 73.1 mm width variants are parameter holdouts in the same generator family, not independent-lineage proof. These are repeated controls within one feature family.

Execution took 1,511.17 seconds (25.19 minutes), from the first recorded worker start to the last completion. From scope preparation to the last completion it took 26.91 minutes. Publication work is separate.

## Native and strict outcomes

- SOLIDWORKS: 23 complete batches / 69 qualified source files strictly decoded. All cuboid volumes match native measurements. Twenty-four world centroids match; 45 top/right placements remain wrong on the main decoder. Batch 020 failed before its after-control; both saved files separately strictly decode but have no complete-batch numerical qualification.
- Fusion: 24 complete batches / 72 source files. Thirty-six strictly decode and match native cuboid volume and centroid. Thirty-six retain the explicit identity-placement refusal: both XZ signs and reverse YZ.
- Committed replay: all 111 SOLIDWORKS inputs strictly decode; Fusion has 72 strict decodes and 72 retained refusals. Source bytes and canonical corpus receipts are retained.

Thus 398 available planned inputs were inspected: 290 strict decodes and 108 strict refusals. One expected native file is missing. No partial fallback was used. Successful decoding does not clear the placement, semantics or vendor-acceptance gaps.

`Comparisons.json` uses bounds-derived volume and midpoint only because these sources are independently API-authored ordinary cuboids. This is not a general geometry or mass-properties algorithm. Source hashes bind every numerical comparison. Explicit neutral mass-property recovery and complete feature constraints remain unqualified.

## Conversion integration

[PR 270](https://github.com/TryUniCAD/Kit/pull/270) owns the timestamped principal-plane attachment repair. Its exact candidate `78a1367e81b5748702289c2b2e733f24576df46e` passes all 69 new complete-batch SOLIDWORKS files in full and design-only public SDK modes: 138 comparisons, zero failures. Checks cover body count, cuboid volume/area/centroid, dimensions, source plane ownership and extrusion direction. `Candidate270Qualification.json` and `Candidate270Source.json` bind that separate candidate. This package does not copy its implementation or substitute its outcomes for the failing main baseline.

[PR 269](https://github.com/TryUniCAD/Kit/pull/269), at `86161a2e8919c0a4fc83ce08ed23d6892f841894`, owns the remaining Fusion refusal investigation. This campaign adds fresh decimal XZ-positive, XZ-negative and YZ-negative controls for its next reader qualification. No Fusion guard was removed and no new writer was added. SOLIDWORKS remains read-only on this baseline; portable generative writing and bidirectional editable acceptance remain open in the conversion backlog.

## Recovery and desktop visibility

Setting an application resource unavailable invalidated batch 008's local controller lease during the desktop pause. Its native request nevertheless completed. Files were retrieved from its original request identifier; no native resubmission occurred. The original controller failure remains in `ControllerStatus.json` and `RecoveryEvidence.json`.

Batch 020 lost its COM/RPC connection; cleanup also reported an unavailable RPC server. Supported recovery succeeded and the three never-dispatched batches 021–023 completed afterward. The failed batch was not replayed. This does not identify or repair the underlying SOLIDWORKS crash.

The user requested unobtrusive desktop operation. A reversible patch to the private process launcher requests hidden startup and hides windows belonging only to the launched process. Both apps passed three-file canaries and final checks found zero visible owned windows. This is hidden desktop automation, not a headless CAD runtime. Backups remain on the PC. `HiddenWindowEvidence.json` records source fingerprints and the provenance limit: the exact external worker revision was not independently bound per batch. Do not infer it from local receipt start times.

## Inspect and reproduce

`Manifest.json` hashes the published artifacts. Native CAD files retain their original bytes. Ground-truth JSON uses LF line endings for publication; its original byte hash is recorded. Documents and large receipts are deterministically gzip-compressed. Public receipts normalize private paths and omit transport credentials, request identifiers, nonces and process identities. Original receipts, exact private commands and full controller state remain in `/tmp/KitNativePlacement-20261123` on the originating laptop; their hashes are retained where applicable.

```sh
python3 re/NativePlacement2026/Verify.py --output /tmp/NativePlacementVerification.json
gzip -dc re/NativePlacement2026/Reports/solidworks-000/variation.json.gz
kit decode re/NativePlacement2026/Cases/solidworks-000/variation.SLDPRT -o /tmp/NativePlacementRead.json
```

Reproduce the separate candidate comparison by extracting `src/` from the exact PR 270 revision into an unused directory and running:

```sh
python3 re/NativePlacement2026/CheckCandidate.py --sdk-root /path/to/extracted-sdk --revision 78a1367e81b5748702289c2b2e733f24576df46e --output /tmp/NativePlacementCandidate.json
```

The candidate source inventory must match before relying on that reproduction. Source authoring and mass measurements were fresh; the candidate comparison was offline. No target application conversion, edit/rebuild/reopen acceptance, independent-lineage generalization or losslessness is established.
