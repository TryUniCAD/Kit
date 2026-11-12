# Native appearance references can resolve to a compatibility partner

A body's appearance `assetReference` need not identify the instance whose definition and library IDs appear in that same body value. A native saved package can store a legacy `Generic` appearance at the base identity and the current appearance at the exact base identity plus `_Post2015`.

Fusion's material catalog hydration invokes `AssetDeSerializer::ResolveAssetReference` with priority 2. If both instances exist, it selects the suffixed instance and gives that instance the base reference as its runtime name. If the base instance is missing, the suffixed instance alone does not resolve.

Apply this specific resolver before checking the selected asset's role, definition and library. Preserve both persisted instances when regenerating the package. Do not bypass those checks or search for any asset with a matching definition. The [native binary evidence](../../../../../re/Fusion/Reconstruction/OgsScene/MaterialAliasEvidence.json) records the resolver, its vtable slot, both priority-two call sites, and the suffix literal; [native document links](../../../../../re/Fusion/Reconstruction/OgsScene/NativeMaterialLinks.json) show the paired identities in both controls.
