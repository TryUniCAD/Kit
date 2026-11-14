# SerializeMap 2025 to 2026 differences

`re/data/Serialization/SerializeMap.json` is the 2025 `sldmodu.dll` map (vtable slot 5 = `Serialize`).
`re/data/Serialization/SerializeMap2026.json` is regenerated from the 2026 SP05.2 DLLs with
`re/tooling/sw2026/SerializeMap.py` over Ghidra vtable dumps of `sldmodu.dll`, `sldmfcu.dll`,
`sldarchiveu.dll` and `sldvisualstateu.dll` (each entry names its DLL).

- `sldmodu.dll` classes: 2025 2607, 2026 2601.
- Added in 2026 (3): `moSkDimHandleLogGroup_c`, `sgLogGroupDim`, `solvLogGroupG`
- Removed in 2026 (9): `CTypedPtrArray<su_CPtrArray,moChainComponent_c*___ptr64>`, `CTypedPtrArray<su_CPtrArray,moTbStackHoleFeatRef_w*___ptr64>`, `moStackDiameterRelation_c`, `moStackRelation_c`, `moTbStackComponentData_c`, `moTbStackComponent_c`, `moTbStackHoleFeatRef_w`, `suTypedPtrArray<moChainComponent_c>`, `suTypedPtrArray<moTbStackHoleFeatRef_w>`
- Classes present in both with a different vtable length: 5.

`Serialize` addresses differ for almost every class because the image layout changed; only class
membership and slot positions carry over. Every 2026 schema is translated from the 2026 address.
