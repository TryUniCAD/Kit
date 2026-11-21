# Preserved serialize maps are version specific

`re/data/Serialization/SerializeMap.json` is a preserved older-build map. Its familiar class names do not bind its addresses to the installed 2026 build.

The ordinary linear-pattern investigation initially selected those preserved addresses. Original 2026 bytes and PE function bounds immediately disagreed; the attempt was rejected before any schema or construction change. The correct source was `SerializeMap2026.json`, then independently checked against actual vtable `+0x28`, complete RTTI hierarchy and full exception-directory bounds. The [field record](../../../../../re/solidworks/records/LocalLinearPatternOwnership2026.md) retains the failed lookup and exact current identities.

Choose the release-specific map, hash it, and verify actual dispatch in the exact pinned module before using a recorded address. A nearby export label, an identically named class or an old offset is insufficient. Keep missing nullability/type-check bodies explicit when a reached MFC ordinal has not independently been bound in the actual architecture.
