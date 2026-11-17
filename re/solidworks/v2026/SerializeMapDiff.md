# SerializeMap 2025 to 2026 differences

The [2025 map](../../data/Serialization/SerializeMap.json) inventories `sldmodu.dll` and stores its slot-5 serializer entry points. The [2026 SP05.2 map](../../data/Serialization/SerializeMap2026.json) covers `sldmodu.dll`, `sldmfcu.dll`, `sldarchiveu.dll`, `sldvisualstateu.dll`, `sldmopartu.dll` and `sldasmu.dll` and names the module for each entry. The [map generator](../../tooling/sw2026/SerializeMap.py) consumes vtable dumps with its existing output and `module=path` arguments.

## Observed inventory differences

The `sldmodu.dll` maps contain 2,607 and 2,601 entries respectively, with 2,598 shared classes. The [deterministic receipt](SerializeMapDiff2025To2026.json) lists 3 names present only in the newer `sldmodu.dll` inventory, 9 only in the older inventory, and all 5 vtable slot-count changes. All 2,598 shared serializer addresses differ, and 1,733 recorded labels have different spellings. The five auxiliary modules are included in the 2026 inventory only, with 691 entries including 24 alternate entries. These are coverage and dispatch observations. The receipt makes no wire changes claim.

Run the offline byte check from the repository root. To regenerate the receipt, use `--output` with the same destination.

```sh
python re/tooling/sw2026/CompareSerializeMaps.py \
  re/data/Serialization/SerializeMap.json re/data/Serialization/SerializeMap2026.json \
  --older-default-module sldmodu.dll \
  --check re/solidworks/v2026/SerializeMapDiff2025To2026.json
```

## Independently verified wire observations

The authored source corpora verify `_MO_VERSION_18000` in the 2025 documents and `_MO_VERSION_19000` in the 2026 documents. The 2026 corpus also uses `swVersion="19000"` in `swXmlContents/Features` and `_DL_VERSION_19000`. The authored ladders put the configuration feature-count observation at byte 1414 in 2025 and byte 1610 in 2026. Those coordinates apply to the corresponding ladders. Container version 4, nibble-swapped names, raw deflate, the ordinary archive tag and map-counter rules, and the `0x86`/CRLF KeyWords framing were reverified on 2026. These results come from the separate [corpus and native re-verification](Reverification.md). [Adjacent release qualification procedure](../records/AdjacentReleaseQualification.md)
