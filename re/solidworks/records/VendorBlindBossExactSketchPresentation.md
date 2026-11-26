# Compose an exact sketch with Top and plane visibility

Use the [complete combined request](../measurements/2026/EncoderRoundTrip/Requests/ExactSketchWithPresentation.json) in a fresh process. To replay the companion candidate, change only `show_construction_planes` to `false` and encode the modified request as canonical JSON.

```powershell
python -I -B re/solidworks/EncoderBoundary/ComposeExactSketchPresentation.py --request <request.json> --locator 'C:\KitEncoderRoundTrip\reconstruction.SLDPRT' --epoch 1785626030 --output <new-output-folder>
```

The request uses `schema` equal to `kit.research.exact-sketch-presentation.v1`, one typed metre `document`, and `display_units` equal to `mm`. `annotation_view` carries the [existing exact Top request fields](../WriterResearch/TopAnnotationCandidate.md) for the sole active configuration. `show_construction_planes` is a JSON Boolean. The generator needs the persisted JSON, explicit locator and write epoch. The locator stem must match the modeled name.

The SI plan owns the exact line and D1 values. The physically converted millimetre view supplies display settings and passes the ordinary planner and part input checks. The shared generated graph owns the `*Top` occurrence in `moPart_c.fa48`, and the ordinary Definition recipe writes the global plane preference at low-word bit 17. The optional native display mask override remains outside this scope. [Exact sketch validation](VendorBlindBossExactSketch.md) · [Plane field and native controls](https://github.com/TryUniCAD/Kit/pull/308) · [Plane qualification](https://github.com/TryUniCAD/Kit/pull/310)

Compared with the exact-sketch control, adding the Top view changed only `Config-0` and its linked resolved-feature stream. Switching the plane setting changed only one byte in `Contents/Definition`. Both variants retained the eight authored XY words, exact SI D1, MMGS display and MKS analysis tables, and one six-face solid. Config-0 and resolved-feature reads retained the same object identities at their map boundary. The Top matrix retains both negative zeros. The saved pose and subtype match the previously measured default Top shape. Native hidden state and other native behaviour for the combined candidates still require a fresh oracle. [Offline candidate digests and readback](../measurements/2026/VendorBlindBossExactSketchPresentation.json)
