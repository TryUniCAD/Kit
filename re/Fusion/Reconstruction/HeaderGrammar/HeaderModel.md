# Native Metadata Header Semantics

The two 32-bit fields previously retained as `MetaHeader.HeaderWords` are one 64-bit saved software version. The native serializer calls `SegmentImpl::lastSavedSoftwareVersion` and writes the result as a 64-bit integer. For the controlled build, `(17, 709361728)` is `0x2a48004000000011`, representing version 2706.1.17.

`Ns::SoftwareVersion::VersionInfo` constructs the value as `(major << 50) | (minor << 38) | build`. The accessors use 14 bits for major and 12 for minor. The constructor's build argument and the accessor result are unsigned 32-bit, leaving bits 32–37 unused in newly constructed values despite the accessor's nominal 38-bit mask.

The wide UUID previously called `Namespace` is the segment's `currentVersion`, not an arbitrary text namespace. The save code emits literal magic 1234, current persisted metadata version, the packed software version, segment type identifier, add-in identifier, and `SegmentType.neutronType`.

The next word is an ancestry UUID count. A nonzero count is followed by that many wide UUID strings. The same vector at `SegmentImpl +0xa8` is emitted here and scanned by `isDescendedFrom`. The qualified controls have no ancestry entries. The current production header codec admits this zero-count profile and should not be described as supporting arbitrary ancestry.

[NativeHeader.json](NativeHeader.json) records source and thin-image digests and bounded disassembly excerpts. Some native accessors share folded machine-code addresses with unrelated functions; the complete symbol table identifies `lastSavedSoftwareVersion` at `0x1e1848` and `currentVersion` at `0x1d26fc`, even when a disassembler chooses another alias.

`InspectHeader.py` recreates the evidence using static tools only. Thin the universal image before ranged disassembly: the installed tool ignored range limits when reading the universal image with `--arch=arm64` and emitted its complete text section instead.
