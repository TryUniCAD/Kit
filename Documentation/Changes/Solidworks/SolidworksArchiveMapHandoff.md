# SOLIDWORKS archive map handoff

The 2026 research serializer can now carry class and object maps from a
configuration into its resolved-feature stream. The next map counter is
computed from the emitted graph, and object references retain their identity.
This follows the native archive-cache copy operation rather than assigning a
base from a feature-count formula.

Use `Load.map_state()` or `Store.map_state()` to obtain an `ArchiveMap`.
`ConfigPart.store_config_state` returns configuration bytes and that map;
pass it as `seed` to `ResolvedCore.store_resolved`. A mismatched base fails
explicitly. The research CLI's `--link-config` mode checks the handoff through
real source configuration/resolved stream pairs in remote CI.

Resolved document context now reads part/assembly identity and the saved
configuration manager flag instead of forcing the ladder's part defaults.
The shared dimension grammar also recognizes the constructor-backed
`moLengthParameter_c` subclass through the existing double-parameter schema.

See the [2026 evidence table](../../../re/solidworks/records/ArchiveMapConstruction2026.md)
for module addresses and limits. Static syntax and formatting are the local
checks; linked-stream process verification is pending remote CI. No tests
ran locally. This adds no production writer and establishes no native-output
acceptance; the [adapter guide](../../Reference/Adapters/Solidworks.md) remains
read-only.
