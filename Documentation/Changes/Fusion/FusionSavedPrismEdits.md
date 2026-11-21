# Read native saved rectangular extrusion edits

Fusion can save an edited rectangular extrusion with four-byte ASM integers and allocated topology entity tags. The typed prism reader previously required eight-byte integers and empty topology tags. The document reader also rejected a saved nonzero rectangular taper.

The reader now preserves the stored integer width and entity tags. It validates a drafted rectangle against independently generated caps, walls, volume, centroid, area, and inertia. The driving taper parameter remains attached to the extrusion definition. Production decoding does not call a CAD application or load research fixtures.

Snapshots retain separate solid, selected-region, and sketch-sheet roles. A fourth body is accepted only as a separate retired rectangular sheet: its passive identity precedes the current identities, every record has a qualified owner, and its original curve tags remain intact. It does not become another physical document body. Stale dimension extension coordinates remain presentation data; measured dimension carriers and driving values must still agree.

## Usage

```sh
kit decode re/Fusion/Reconstruction/NativeEditedPrisms/Width.f3d --output /tmp/width.json
kit decode re/Fusion/Reconstruction/NativeEditedPrisms/DraftNegative.f3d --output /tmp/draft.json
```

`PrismHistory.Tracking` stores typed topology entity identities. `EmitPrismHist` accepts this optional tracking model. Document history and snapshot serialization preserve a stored four-byte header.

## Verification

Fusion 2706.1.17 opened and rebuilt the existing P03 control, independently changed width, height, depth, and taper, saved each edit, and reopened each file in a fresh process. All five sets of 27 comparisons passed, between healthy before/after controls. The source inventory remained unchanged during the batch.

Eight additional vendor-authored controls cover positive, negative, small, and steep taper, both with unchanged dimensions and with independent width, height, and depth changes. All 216 comparisons against recorded native measurements passed. Twelve first-party native files and their independent measurements are retained in [the evidence directory](../../../re/Fusion/Reconstruction/NativeEditedPrisms/Findings.md).

The new CLI compatibility coverage runs through public decoding, offline measurement comparison, and typed history serialization. It runs in remote CI; no local test suite was run. PR and merge-group CI results remain separate from the live native evidence.

## Limits

This change qualifies the bounded anchored XY rectangular extrusion reader. It does not add a SOLIDWORKS writer, a general drafted-profile writer, arbitrary snapshot families, or cross-format conversion acceptance. Existing conversion-readiness guards remain active. SOLIDWORKS semantic comparison is a separate unresolved scope.

See [saved ASM width and topology identities](../../Gotchas/Conversion/Fusion/Geometry/SavedPrismIntegerWidth.md) and [retired snapshot sheets](../../Gotchas/Conversion/Fusion/Geometry/RetiredPrismSheets.md).
