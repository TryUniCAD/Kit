# Through-all source owner components

The internal source projection retains a complete ordinary SOLIDWORKS source while constructing only its supported geometry owners. It does not convert or write a complete native file.

Use `ProjectThruSrc(document, output_name)` on the complete normal SDK read. The result has two channels:

- `EnvelopeValue` retains the actual original document, every timeline identity, all metadata and all unsupported source fields.
- `InputValue` contains only typed geometry, names, units and semantic owner IDs. It contains no native payload or captured field program.

Pass the typed input and explicit target settings to `MakeThruOwners`. The result exposes fresh system, stock profile, boss, cut, scope and source-correspondence objects. It is a component graph, not a `PartCandidate` or serialized file. The source envelope remains attached to the source plan and must be preserved by any caller that retains this projection.

The measured profile has four real stock lines and unary relations, one free circle with its distinct centre, two actual sketch-normal selections, both profile dependencies, native stock `join`, three principal datums, one actual total stock-depth driver and one selected stock. Fresh native IDs and indexes follow the generated graph. An explicit correspondence retains source lines whose individual orientation opposes the canonical generated contour.

`RequireThruFull(envelope)` currently refuses complete source construction. It recomputes the missing fields from the original document. Clearing a stored status does not qualify the source. Style, scene, configuration settings, owned presentation, provenance, native sketch state, body-caption authority and continuous automatic selection remain open. Source metadata and native payloads are observation-only.

The final portable body belongs to the cut. The cold selected atom belongs to the preceding stock. The component records the final body as pending regeneration instead of assigning it to that stock atom. See the [gotcha](../../../../../Gotchas/Conversion/Solidworks/Model/ThroughAll/SourceFinalBodyIsNotStockAtom.md).

The [field record](../../../../../../re/solidworks/records/ThroughAllSourceOwners2026.md) and [68-process receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllSourceOwners01.json) define the scope and exact source hashes. The source-only proof covers three disclosed reads, deterministic guarded generation, six partial archive roles, actual linked aliases, unsupported-input refusals and unchanged legacy callers. It starts no CAD application, opens no hidden case and grants no native or public writer qualification.
