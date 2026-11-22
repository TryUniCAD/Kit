# A native part can carry a binary-only property manager

`Contents/CusProps` is a property owner in its own right. Treat a
present manager as input even when the summary, custom and
configuration XML scopes are absent. Validate the entire manager
against the version-specific empty profile before allowing writes.

The disclosed binary-only variants keep their geometry and feature
history. The compatible empty manager adds no property-specific
restriction. The model may still have a separate portability refusal.
An unsupported manager leaves an inspection diagnostic and blocks
publication through the registry after either strict or relaxed
inspection.
[Binary-only controls and write proof](../../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md#binary-only-owners-and-registry-write-policy)
