# Saved parts can carry a direct Sheet-Metal Master

The selected two-stock original saves one empty Exploded Views manager in Config-0. After SOLIDWORKS rebuilds and saves the generated two-stock model, Config-0 also has an empty Sheet-Metal Master. The saved public tree carries both rows.

The Sheet-Metal Master is a direct schema-one `moSheetMetalMaster_c` under `moPart_c.f1018`, selected by `f1014=1`. It has public ID `−1`, no stored name or children, `n370=0`, and an empty `f358` body list. Its direct serialization gives it no archive map index. The separate `f13f8` Exploded Views manager still has a tagged identity in the linked map.

Validate the direct master through its part field and retain its public row. Resolve the tagged helper and the six cabinet and environment members against the actual linked map. Populated helpers, a map index on the direct master, and an unmatched public row all refuse the two-stock presentation check.

[Linked ownership receipt](../../../../../../re/solidworks/measurements/2026/TwoStockSavedPresentation01.json) ·
[Native edited save receipt](../../../../../../re/solidworks/measurements/2026/TwoStockColdNative01.json)
