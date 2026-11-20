# SOLIDWORKS empty file property owner

The internal part property model accepts an explicit empty native file owner.
The shared version-19000 archive serializer constructs the property manager,
its key-zero entry and the empty file container. The owner has no
cut-list container. Its binary stream is independent of summary, document
and configuration XML scopes.

Three disclosed local imports produce the same 102-byte property stream as
their native source through guarded construction with no runtime file reads.
Disabling only that owner removes only `Contents/CusProps`. The process
coverage reads both XML-only and binary-owner parts through the public SDK.
The pre-writer locked native lifecycle and public writer admission are
separate checks.

[Property owner field order](../../../../../re/solidworks/records/PartEmptyAdvancedProperties2026.md)
· [Sealed evaluation procedure](../../../../../re/tooling/sw2026/imported_body_source/StageSealedImportedGeometry.py)
