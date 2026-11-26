# Compose an exact sketch with Top and plane visibility

Use the [complete combined request](../measurements/2026/EncoderRoundTrip/Requests/ExactSketchWithPresentation.json) in a fresh process. To replay the companion candidate, change only `show_construction_planes` to `false` and encode the modified request as canonical JSON.

```powershell
python -I -B re/solidworks/EncoderBoundary/ComposeExactSketchPresentation.py --request <request.json> --locator 'C:\KitEncoderRoundTrip\reconstruction.SLDPRT' --epoch 1785626030 --output <new-output-folder>
```

The request uses `schema` equal to `kit.research.exact-sketch-presentation.v1`, one typed metre `document`, and `display_units` equal to `mm`. `annotation_view` carries the [existing exact Top request fields](../WriterResearch/TopAnnotationCandidate.md) for the sole active configuration. `show_construction_planes` is a JSON Boolean. The generator needs the persisted JSON, explicit locator and write epoch. The locator stem must match the modeled name.

The SI plan owns the exact line and D1 values. The physically converted millimetre view supplies display settings and passes the ordinary planner and part input checks. The shared generated graph owns the `*Top` occurrence in `moPart_c.fa48`, and the ordinary Definition recipe writes the global plane preference at low-word bit 17. The optional native display mask override remains outside this scope. [Exact sketch validation](VendorBlindBossExactSketch.md) · [Plane field and native controls](https://github.com/TryUniCAD/Kit/pull/308) · [Plane qualification](https://github.com/TryUniCAD/Kit/pull/310)

Compared with the exact-sketch control, adding the Top view changed only `Config-0` and its linked resolved-feature stream. Switching the plane setting changed only one byte in `Contents/Definition`. Both variants retained the eight authored XY words, exact SI D1, MMGS display and MKS analysis tables, and one six-face solid. Config-0 and resolved-feature reads retained the same object identities at their map boundary. The Top matrix retains both negative zeros. The saved pose and subtype match the previously measured default Top shape. Native hidden state and other native behaviour for the combined candidates still require a fresh oracle. [Offline candidate digests and readback](../measurements/2026/VendorBlindBossExactSketchPresentation.json)

## Replay the captured configuration name

Starting from the tracked On request, set `request["document"]["configurations"]["$tuple"][0]["name"] = "Default"`. Keep the configuration ID, Top frame and `show_construction_planes: true`. Use `EncoderRoundTrip.Artifacts.canonical_json` to persist the modified request and run the same command in a fresh process. The request SHA-256 is `cdefa9be027d8257c0f5b08cf722efff746f38960b86e5e73eac2e63bf7d1ac4`. The candidate SHA-256 is `2d027288f37b8bffe90dc289842913b9c4ca807942fe6b32ad1eb7fea5acea29`.

The previously recorded StockBefore phase observed the exact Author04 source with `Default` active, both global plane getters true, and one assigned hidden Top-oriented view before and after rebuild. The generated candidate resolves `Default` as the sole active neutral configuration and agrees with configuration ID 0 in the typed `CMgrHdr2` directory and the keyword row. Compared with On, the name-only edit changed `CMgr`, `CMgrHdr2`, `Config-0-ModelHeader`, `Header2`, and `KeyWords`. The Config-0 and resolved-feature stream bytes were identical to On. Strict SDK readback reported the same geometry.

The source has 36 clear streams and the candidate has 10. Written configuration names agree with the captured source state, while complete manager ownership and original source provenance still need separate treatment. The source MMGS length precision is two decimals and the generated recipe's is four. The source analysis-unit table is absent and the generated part supplies MKS. Full native `GetUnits` formatting, the runtime display-state name and the combined appearance remain outside this offline result. [StockBefore provenance and typed comparison](../measurements/2026/VendorBlindBossExactSketchPresentation.json) · [Display-unit table gotcha](../../../Documentation/Gotchas/Research/Writers/SolidworksMmgsFormattingNeedsItsOwnProof.md)

## Compare document unit precision

Use the captured-name request above without further edits. Set `$request` to its canonical JSON path and `$out` to a new scratch directory outside the checkout. The four generation calls below start fresh offline processes. Their input is the request, locator, epoch and optional command precision. The last call alone reads the retained native Author04 `BaselineSource.SLDPRT`. Set `$stock` to that file from the stock evidence holder. The comparison verifies its SHA-256 before decoding it. [Stock capture provenance](../measurements/2026/VendorBlindBossExactSketchPresentation.json)

```powershell
New-Item -ItemType Directory -Path $out
$arguments = @('--request', $request, '--locator', 'C:\KitEncoderRoundTrip\reconstruction.SLDPRT', '--epoch', '1785626030')
$precisionTool = 're/solidworks/EncoderBoundary/CheckBossUnitFormat.py'
python -I -B re/solidworks/EncoderBoundary/ComposeExactSketchPresentation.py @arguments --output "$out/Default"
python -I -B $precisionTool generate @arguments --precision 4 --output "$out/Explicit04"
python -I -B $precisionTool generate @arguments --precision 2 --output "$out/Precision02"
python -I -B $precisionTool generate @arguments --precision 2 --output "$out/Precision02Repeat"
python -I -B $precisionTool compare --control "$out/Default" --explicit-four "$out/Explicit04" --precision "$out/Precision02" --repeat "$out/Precision02Repeat" --stock $stock --stock-sha 02cc9e0ea4b2cebe3b99d908180b409f1ceeffd5cbef13d2a9685caaf4d8ca7d --control-sha 2d027288f37b8bffe90dc289842913b9c4ca807942fe6b32ad1eb7fea5acea29 --output "$out/Comparison.json"
```

The recorded run used CPython 3.14.6 AMD64 with zlib-ng 1.3.1. The default and explicit-four archives and their strict readback receipts were byte-identical. Both precision-two runs produced SHA-256 `320bfb382e77dbb3296da19dd0478fdf939cdcefd271e25908a460b322f26026`. Precision 17 exited 2 before creating an output directory. Supplying the same precision-two directory as both replay results exited 1 without a comparison. The constructor audit detected zero external access attempts. [Exact comparison](../measurements/2026/VendorBlindBossUnitPrecision.json)

The clear Config-0 stays 22,540 bytes and changes only at the first byte of each of the sixteen document-unit `f0c` words. The other nine clear streams and all sixteen analysis-unit rows match. Strict SDK readback verifies the linked exact SI sketch and D1, the signed Top frame, the plane-visibility word and the same directed solid with six faces, twelve edges, eight vertices and 7,584.3 mm³.

Author04 also stores two in every top-level `f9b8.f0c`. Fourteen complete rows agree with the two-place candidate. Length differs in `f18` (0.1 and 0.01), `f20` (4 and 10), `f28` (8 and 1) and the typed `fb8` override with code 3 that only the source retains. The density `fcc` values are 0 and 1. Author04 has no `f9c0` table. The writer deliberately retains its required distinct MKS table. These are confirmed typed and wire observations for the two archives. The meaning of the residual fields and the effect of absent analysis units still require qualification. [Existing unit-table grammar and independent controls](ConfigUnitTableSlice2026.md)

Prior native `GetUnits` captures were `[0, 1, 8, 2, 0]` for Author04 and `[0, 1, 1, 4, 0]` for the four-place generated recipe. SOLIDWORKS documents the third value as the denominator for fractional inches or feet-inches. The decimal millimetre contrast should retain that raw value for evidence and interpret the fourth value as decimal precision. A native length-only contrast should set `swUnitsLinearDecimalPlaces` with the document extension, retain angle and mass preference readings, and capture the full unit tuple before and after the edit, save and fresh reopen. Native observations for this exact two-place archive are pending. [Prior native readback](https://github.com/TryUniCAD/Kit/blob/ad4d64c025c3e19a7c71e95984af2248d5945886/re/solidworks/records/VendorBlindBossNativeSketchProof.json) · [SOLIDWORKS GetUnits](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~GetUnits.html) · [Units preferences](https://help.solidworks.com/2024/english/api/swconst/DP_Units.htm)

## Verified native unit precision

The two exact files from the existing typed recipe replay opened read-only and rebuilt. The sources remained unchanged and stock controls passed before and after the generated pair. The exact length unit was millimetres. The whole `GetUnits` values are preserved in the evidence along with 24 independently queried document preference results. [Compact native proof](VendorBlindBossNativeUnitPrecisionProof.json)

| Fresh process | Active seconds |
| --- | ---: |
| Stock before | 11.691 |
| Generated four-place | 12.623 |
| Generated two-place | 14.609 |
| Stock after | 13.543 |

The four-lifetime group took 55.642 seconds. All owned exits were normal and all open diagnostics zero. Two-place and four-place generated structures match outside units. Raw XY, aliases, exact D1, Top and plane state survive open and rebuild. The two-place native getters match stock except for the stored fraction denominator. Measured case-specific numeric roundoff remains recorded. The result does not test the length-only native setter or change either generated archive.

Retrieve the verified private package at `D:/KitRuns/EncoderSwBossRea20261125/BossUnitFormat/NativeEvidenceCompanion01/PrivateNativePrecisionEvidence.tar.gz`. The compact proof gives its SHA-256 and the digest of the private member map. Verify both before extracting into an unused private directory, then check each of the 41 member sizes and hashes. The retained source, candidates and native records remain separate from the path-free report. Licensed software and the original template are identified by their hashes only.
