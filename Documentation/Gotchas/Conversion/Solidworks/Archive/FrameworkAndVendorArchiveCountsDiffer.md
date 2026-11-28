# Framework and vendor archive counts have different escapes

## Expectation

Every count in the SOLIDWORKS archive can use the same helper because framework and vendor serializers share archive infrastructure.

## Actual behavior

The pinned `swccu.dll` string-to-int map calls framework MFC count imports. Their reached implementations read u16, escape `0xffff` to u32, then escape `0xffffffff` to u64. Native store uses the corresponding canonical thresholds. The complete reached bodies and effective mapped-byte equality are bound in the [native field record](../../../../../re/solidworks/records/MfcCountArchive2026.md).

Vendor `su_CArchive` count uses u16 and one u32 escape only. Its u32 value `0xffffffff` is an ordinary count, not another marker. Applying the framework rule globally would consume the next eight payload bytes on that vendor path and corrupt field alignment. Applying the existing vendor rule to the framework map would miss a legitimate wide-count escape. Empty or small maps cannot distinguish those two grammars.

The framework reader also accepts overlong forms, while its writer chooses canonical width. The integer alone does not preserve a noncanonical wire width. No arbitrary overlong-count byte identity is established by the new owner.

## Workaround

Select the count operation from the exact native call boundary. [MfcMaps.py](../../../../../re/tooling/sw2026/serial/defs/MfcMaps.py) supplies the separate framework operation for the proven ordinary-version-19000 map owner. Preserve the vendor `Core.count_value`, `Schema.Cnt` and `Dsl.count` grammar for existing owners. Preserve `n/items/k/v`, shared CString/i32 rows and the existing decoder repetition limit; native u64 capacity is not permission to allocate that many rows.

The new owner requires ordinary Core load/store types and current effective version. It does not interpret unrelated `conditions` metadata as a native mode flag or claim DB support. The [change entry](../../../../Changes/Solidworks/Model/SolidworksMfcCountArchiveOwner.md) records actual evidence and pending remote replay. Neither count-family selection nor byte equality establishes fresh model acceptance.
