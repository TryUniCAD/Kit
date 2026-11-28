# Signed identity keys do not define hash-map iteration order

The edge lookup table writes signed 32-bit keys, while the face table writes unsigned keys. Sorting either table by that scalar type would infer an ordering rule the native implementation does not use.

Pinned SOLIDWORKS 2026 selects the two separate tables, then inserts through the same raw-four-byte FNV-1a hash helper. Both tables start with eight buckets and maximum load one. The fresh twelve-edge sequence `7..18` grows to sixty-four buckets before the ninth edge is linked. Rehash preserves its existing list because all destination buckets are empty, and the pending edge recomputes its bucket after growth. The serializer walks that forward list, yielding `7..18` in this scoped member.

The native read route separately reserves from the incoming count. Twelve loaded rows can therefore begin with sixteen buckets rather than the fresh incremental table's sixty-four. Neither capacity is emitted as the list order.

Derive insertion, growth, rehash and forward-list traversal from their actual source branches. Preserve the scalar wire type independently. Refuse collision histories outside the proved member; do not generalize this ascending result into a sort. [Exact source and bounded numeric replay](../../../../../../re/solidworks/records/DownstreamEdgeRegistrationOrder2026.md)

This is static/numeric construction evidence only. No native cache load, regenerated edge wrapper or vendor acceptance is established here.
