# A sketch block map refers to its own manager

The ordinary sketch block manager serializes its feature base and
16-byte GUID before its embedded block map. The map's `f30` field can
refer to the manager itself. The active part map allocates that manager
before it reads the body. The ladder control resolves the backlink to
object slot 98.

Use the owning archive's current map counter and preserve object
identity through body descent. An empty sketch block map still needs the
observed backlink in this bounded profile. The concave control has an
absent manager and consumes only a null tag.
[Native field order and map observations](../../../../../../re/solidworks/records/ConfigFieldActionsSlice2026.md)
