# Vertex reference suffix uses an incident edge ID

## Expectation

The fourth drawing identity word of a vertex reference stores that vertex's node ID, or the value returned by the nearby downstream-attribute getter.

## Actual behavior

In pinned SOLIDWORKS 2026 `moVertexRef_c::Serialize`, the non-detailing drawing store branch obtains the first incident edge of the actual cached vertex. It calls that edge's `gcEnt_w::getNodeId` and passes the result to index 3 of `setRefEntityPersistantID`. The indexed setter writes `ff8[index]`, so this value reaches `f104`. The earlier downstream-attribute getter's return is not used as the setter argument.

This pre-store update requires an actual drawing context, a nonzero valid cached vertex and a nonempty incident-edge list. Ordinary part serialization does not append these four drawing words.

## Workaround

Retain the actual typed words for raw read/write. Do not generate `f104` from the vertex node ID, a body-local index, or the downstream ID. Incident-edge list order and the other drawing identity words require separate model rules before generation.

[Source rules and exact module/interval pins](../../../../../../re/solidworks/records/DownstreamEntityReferenceWire2026.md) bind the call chain `0x4bbaa903 → 0x4bbaa91f → 0x4bbaa942 → 0x4bbaa953`, and the complete 11-byte setter at `0x4b759b00`. Native boundary measurement remains open.
