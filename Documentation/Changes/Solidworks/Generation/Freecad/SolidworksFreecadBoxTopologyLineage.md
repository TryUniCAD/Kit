# Verify portable FreeCAD origin-box topology lineage

`VerifyF14aLineage.py` joins all 26 actual entity roles of each disclosed origin box from the FreeCAD Body and AdditiveBox to the checksum-bound generated and edited SOLIDWORKS parts. Four fresh SDK processes reproduce the result. Each actual saved face identity resolves to its expected cap or producing sketch line, and both complete saved partitions re-emit byte-for-byte. [Lineage audit](../../../../../re/solidworks/records/FreecadF14aTopologyLineage2026.md) · [Exact receipt](../../../../../re/solidworks/measurements/2026/SdkFreecadF14aTopologyLineage01.json)

```sh
python3.14 -I -B re/tooling/sw2026/f14a_lineage/VerifyF14aLineage.py \
  /absolute/path/to/FreecadNewerReleaseNative01 /absolute/path/to/disclosed/fixtures \
  > /unused/external/F14aTopologyReceipt.json
```

The generated inputs have no serialized per-entity kernel identities, and the edited saves contain no previous solid in their rollback. The prior reopen verified geometry and editable owners. Live native persistent-reference resolution and intact-source transfer remain unqualified. [Native reference evidence boundary](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/GeneratedBoxRolesNeedNativeReferenceProof.md)
