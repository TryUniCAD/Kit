# SOLIDWORKS archive tag primitives

The memory-only tag layer in `src/convert/adapters/solidworks/Archive/Tags/` separates nulls, new-class markers, class references, and object references before the archive resolves descriptors or map entries. It depends only on Python's standard library and the shared typed tag value. It reads no files and loads no vendor software.

## Interfaces

`ArchiveTag(KindValue, IndexValue)` is an immutable value. `KindValue` is `Null`, `NewClass`, `ClassRef`, or `ObjectRef`. Structural `Null` and `NewClass` tags require `IndexValue=None`. Reference tags require an integer index from `1` through `0x7fffffff`.

`ReadTag(BufferValue, OffsetValue)` accepts an exact built-in `bytes` value and an integer byte offset, then returns `(ArchiveTag, NextOffset)`. It consumes only the tag: two bytes, or six bytes for an escaped reference. A new-class descriptor remains unread for the higher layer.

`EncodeTag(TagValue)` requires an exact `ArchiveTag` value and returns the canonical little-endian native representation. It writes null as u16 zero and new-class as u16 `0xffff`. Reference indices below `0x7fff` use u16; all larger indices use u16 `0x7fff` followed by u32. Class references set the high bit of the selected reference width.

Invalid input types raise `TypeError`. Invalid tag kinds, structural tags carrying indices, out-of-domain reference indices, negative or incomplete positions, truncated tags, and class index zero raise `ValueError`. Booleans are not accepted as offsets or reference indices. Type annotations do not replace encoder validation.

## Scope and limits

The [2026 grammar record](../../../../re/solidworks/records/ArchiveTagGrammar2026.md) binds the formulas to complete native function extents and hashes. The [escape gotcha](../../../Gotchas/Conversion/Solidworks/Archive/TagEscapesRetainReferenceMeaning.md) describes zero and marker handling.

The reader accepts escaped small references and recognizes escaped object index zero as null. The encoder chooses canonical width, so arbitrary overlong input bytes are not preserved. The returned value does not retain wire width.

The 31-bit reference domain describes the tag representation. Archive map membership, object-versus-class ownership, expected runtime ancestry, schema admission, descriptor encoding, map-counter limits, and object-body serialization remain higher-layer checks. In particular, the native allocation guard is stricter than the wire index domain. Parsing a tag does not prove that its reference exists.

## Verification

The research archive reads every structural tag through `ReadTag`.
Its null, new-class, class-reference, and object-reference writes use `EncodeTag`.
Class descriptors and map allocation retain their existing archive owners.
Field inventories fingerprint all three production modules, and their real CLI process assertions require those exact sources.

Source, AST, and Black checks passed without running a codec, schema, or local test.
An independent original-PE inspection verified six function extents, fourteen unwind fragments, and ten instruction-window hashes.
Remote process checks of this changed implementation remain pending publication.

This internal primitive does not register a SOLIDWORKS writer. Fresh generated files, held-out native acceptance, callback closure, and full feature coverage remain unfinished.
