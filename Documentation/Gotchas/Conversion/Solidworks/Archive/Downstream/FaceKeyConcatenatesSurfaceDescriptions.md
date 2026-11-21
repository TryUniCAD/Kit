# Face key concatenates surface descriptions directly

The ordinary face validator hashes ASCII text starting with `s,`. Each nonnull inline surface contributes its signed decimal words joined by commas. Between surfaces, a cap ending in `0` and a side beginning with `74` produce the adjacent bytes `074`. Null separators contribute no text.

Preserve native inline order and calculate the alternate key by exchanging only slots 1 and 2. Search both keys against the earlier original keys before inserting the current original. [Source and generated replay](../../../../../../re/solidworks/records/DownstreamPrismFaceStore2026.md)
