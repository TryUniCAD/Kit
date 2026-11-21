# Resolved context is document state

## Expectation

A resolved-feature stream can be emitted with one fixed map base and the
context values observed in a saved part ladder.

## Actual behavior

SOLIDWORKS copies the configuration archive's complete map and counter into
the resolved archive. The configuration manager's MBSM flag also controls a
part-only suffix. Fresh manager construction starts that flag at zero;
the researched saved ladder had one. Assemblies do not use the part suffix.

Using the ladder defaults for a fresh graph can therefore duplicate objects,
misidentify class references, or append a suffix that its document does not
require. Matching a sample's byte count would not repair those relationships.

## Workaround

Keep nodes symbolic and carry the actual archive map between streams.
Derive the context from the current configuration manager and model kind.
The [2026 map finding](../../../../re/solidworks/records/ArchiveMapConstruction2026.md)
records the native helper and archive-copy addresses. Linked remote process
verification remains separate from target-application acceptance.
