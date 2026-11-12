# Native Metadata Header Semantics

The two 32-bit fields previously retained as `MetaHeader.HeaderWords` are one 64-bit saved software version. The native serializer calls `SegmentImpl::lastSavedSoftwareVersion` and writes the result as a 64-bit integer. For the controlled build, `(17, 709361728)` is `0x2a48004000000011`, representing version 2706.1.17.

`Ns::SoftwareVersion::VersionInfo` constructs the value as `(major << 50) | (minor << 38) | build`. The accessors use 14 bits for major and 12 for minor. The constructor's build argument and the accessor result are unsigned 32-bit, leaving bits 32–37 unused in newly constructed values despite the accessor's nominal 38-bit mask.

The wide UUID previously called `Namespace` is the segment's `currentVersion`, not an arbitrary text namespace. The save code emits literal magic 1234, current persisted metadata version, the packed software version, segment type identifier, add-in identifier, and `SegmentType.neutronType`.

The next word is an ancestry UUID count. A nonzero count is followed by that many wide UUID strings. The same vector at `SegmentImpl +0xa8` is emitted here and scanned by `isDescendedFrom`. The qualified controls have no ancestry entries. The current production header codec admits this zero-count profile and should not be described as supporting arbitrary ancestry.

[NativeHeader.json](NativeHeader.json) records source and thin-image digests and bounded disassembly excerpts. Some native accessors share folded machine-code addresses with unrelated functions; the complete symbol table identifies `lastSavedSoftwareVersion` at `0x1e1848` and `currentVersion` at `0x1d26fc`, even when a disassembler chooses another alias.

`InspectHeader.py` recreates the evidence using static tools only. Thin the universal image before ranged disassembly: the installed tool ignored range limits when reading the universal image with `--arch=arm64` and emitted its complete text section instead.

## Manifest identity and allocation

[ManifestNative.json](ManifestNative.json) identifies the two root UUIDs as `Document.identifier` and `Document.currentVersion`. The preceding localized strings come from `DocumentType.name` and `DocumentType.description`; they are type labels, not the user-authored document title. The per-module version maps are persisted migrator numbers, bounded against the type's supported migrators.

The asset manifest UUIDs come from `SaveContext.getSavedGuid(asset)` and `Asset.revisionGuid`. The value 5 observed before the segment count is not an unexplained signature. `AssetManifestSaver::doSave` calls `AssetImpl::getNextAvailableSegId(false)` and writes that allocation watermark. The getter reads `AssetImpl +0x48` without incrementing it when passed false. Segment rows then contain `Segment.id`, `Segment.userName`, and `SegmentType.identifier`. A newly authored model must derive the watermark from its allocation policy; a source rewrite must retain any higher watermark left by deleted or transient segments.

## Entity offset ordering

[OrderingCorpus.json](OrderingCorpus.json) observes 2,136 segments across all 712 inventory archives. Their 259,464 primary records and 34,228 continuation records have no descending physical entity IDs. Both metadata index lists also have no descending IDs. There were no unsupported headers or read errors. This is a fresh read-only observation rather than a test run.

[The native loader analysis](../DocumentAuthoring/Variants/BulkOrdering.json) explains the constraint: `BinaryBulkLoadVisitor::buildEntities` traverses the entity-ID tree in order and subtracts consecutive primary offsets to compute chunk lengths. Non-increasing offsets enter the negative-offset error path. Continuations remain within their primary entity chunk. An independently authored ACT graph initially violated this ordering; sorting physical primary records by entity identity advanced native loading to the next semantic requirement.
