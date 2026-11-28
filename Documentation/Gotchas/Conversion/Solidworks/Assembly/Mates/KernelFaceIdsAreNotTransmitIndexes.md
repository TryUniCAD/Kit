# Kernel face IDs are not transmit indexes

The faceted mate snapshot's `f40` might be mistaken for a face's transmitted record index or its position in a neutral face array. The disclosed native cylindrical children demonstrate that these are different identities: the selected face's normalized SDK index changes from `41` to `39` after a depth edit, corresponding to wire indexes and public face suffixes `42` and `40`, while its actual kernel `node_id` and snapshot `f40` remain `27`.

`XmtCursor.ReadIndex` intentionally returns wire index minus one. The public geometry ID uses `NativeId("face", IndexValue + 1)`. Keep that normalization separate from the persistent kernel ID. Historical raw receipts retain their recorded normalized values and hashes.

Resolve the actual cylinder face through its surface, shell, body and feature-owned `FACE_ID_2001` attribute. Use the face's real `node_id` when checking a snapshot. Resolve the body atom independently. Never turn the observed `27` or `101` into a fresh-file constant. Complete saved parsing does not yet explain how the vendor assigns those IDs to a fresh parametric body.

The active wrapper's optional vector is also child-local in these twelve endpoint observations. The rotated D03 case rejects replacing it with the world axis. Its constructor and presence predicate remain unqualified.

[Typed six-child evidence](../../../../../../re/solidworks/records/ConcentricKernelFaceIdentity2026.md) · [Earlier snapshot field binding](ConcentricSnapshotIdsNeedKernelOwners.md)
