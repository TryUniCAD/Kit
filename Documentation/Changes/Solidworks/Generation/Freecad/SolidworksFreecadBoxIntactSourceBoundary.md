# Verify the intact FreeCAD origin-box writer boundary

`VerifyFreecadF14aIntact.py` checks two checksum-bound FreeCAD 1.0.2 and 1.1.4 AdditiveBox originals. It uses normal strict SDK reads, records seven writer or preparer refusals per source, and checks that the path and stream destinations stay untouched. The internal source projector and shared part constructor independently regenerate both previously native-tested files byte-for-byte with zero runtime reads. The receipt includes result digests, all three live driver bindings, the six native payload owners per source, material and appearance distinctions, and the actual Body element-map child records. [Probe](../../../../../re/tooling/sw2026/VerifyFreecadF14aIntact.py) · [Exact receipt](../../../../../re/solidworks/measurements/2026/SdkFreecadF14aIntactSource01.json)

```sh
python3.14 -I -B re/tooling/sw2026/VerifyFreecadF14aIntact.py \
  /absolute/path/to/FreecadOriginBoxSchema01 /absolute/path/to/disclosed/fixtures \
  > /unused/external/F14aReceipt.json
```

The two paths supply the earlier manifest and strict request snapshots and the two original FCStd files. The program prints a scoped receipt with no copied CAD bytes. Four independent SDK processes repeat the results. Intact export remains gated by the native source definition, source-owned topology lineage, native payloads, provenance and round-trip metadata. The comparison adds no new native or held-out qualification. [Owner and guard record](../../../../../re/solidworks/records/FreecadF14aIntactSource2026.md) · [Element-map gotcha](../../../../Gotchas/Conversion/Freecad/ZeroNameCountRetainsChildShapeLineage.md)
