# Attachment downstream storage

The [research record](../../../../../re/solidworks/records/DownstreamAttachmentStore2026.md) binds the conditional SOLIDWORKS 2026 assembly attachment downstream save route, actual cache owner, configuration-derived name and fresh direct-body archive namespace.

Use it alongside the existing part/store/map evidence. The assembly path receives one actual configuration from `SaveModels` and reads its opened model's attachment cache. Failed cache selection returns before touching storage; it does not perform the part method's stale-cache deletion. The preceding attachment stream's maps are not inherited. Templates, autosave and unresolved special contexts remain excluded.

This is source knowledge only. Original-image bounds, hashes, RTTI, imports and selected caller windows were verified statically. No SDK behavior changed, no application or VM ran, and no native or held-out acceptance is claimed. Actual saved-stream replay and concrete live storage-manager selection remain pending.

The [stream-retention gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/AttachmentSaveKeepsUnselectedCacheStreams.md) records the lifecycle difference.
