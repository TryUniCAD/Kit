# Generate canonical native view records

The shared research model now generates ten distinct standard-view records
instead of null entries. Each record contains its canonical name and index,
constructor state, computed orientation and independent identity transform.
The native loader's null fallback restores names and ids without rebuilding the
indexed orientations, which left isometric selection face-on.

The [native construction record](../../../re/solidworks/records/StandardViewsConstruction2026.md)
binds every field, resource name, exact angle constant and operation order to
2026 binaries. The builder computes Hamilton quaternion products and normalized
matrix rows. It reads no vendor resource, DLL, saved view or captured matrix at
runtime. Its effective detail-standard input is explicitly limited to the
currently classified literal one.

The complete-file process harness checks ten distinct decoded view objects,
their ordered ids and rotation-payload presence. Remote CI and new controlled
viewport measurements are pending. Geometry/edit results measured before this
change are retained separately; they do not establish acceptance of its new bytes.
