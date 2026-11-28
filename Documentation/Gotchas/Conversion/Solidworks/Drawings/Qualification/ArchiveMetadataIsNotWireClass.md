# Archive metadata is not a wire class

Typed archive fields can contain SDK metadata objects in addition to actual archive nodes. `ReadSharedFile` attaches a `NativeFileRef`, and `ReadHeaderBody` attaches a `NativeHeader`. A generic JSON reporter that handles only nodes, mappings and scalars can fail after the archive itself loaded correctly.

The first profile-child report stopped on `NativeFileRef` after both child graphs had loaded. The observer now represents those two concrete metadata types explicitly and includes the exact type and field path for future unsupported values. It neither serializes metadata as a native class nor weakens the SDK parser. Preserve the failed report separately from any product conclusion. [Exact failure and corrected receipts](../../../../../../re/solidworks/records/DrawingOriginProfileLinkage2026.md).
