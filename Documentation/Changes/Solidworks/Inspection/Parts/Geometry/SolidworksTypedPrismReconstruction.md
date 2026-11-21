# Typed rectangular-prism geometry without a native cache

The strict SOLIDWORKS part reader can reconstruct a validated neutral B-rep for a complete ordinary version-19000 rectangular blind prism whose source has no physical geometry cache. It uses actual typed contour, support, dimension and feature owners and the existing analytic prism builder. The native source bytes and writer behavior remain unchanged.

Use `convert.open_document(path)` with its default options for the admitted profile. The result exposes `document.brep`, exact body topology and an informational `sldprt.brep_reconstructed` diagnostic. `document.brep_payloads` remains empty because no native Parasolid bytes were stored. `include_brep=False` retains the prior history-only read. No tessellation is synthesized.

The scope requires one independent Config-0, the ordinary system graph, actual canonical Front placement, one fresh axis-aligned four-line contour and one forward blind create boss. Existing qualified width/height drivers and an actual origin coincidence are retained. Other geometry, owners, configurations, end/draft/thin/from modes, reference state and unknown stream roles reject. Present native caches retain their existing decoder and errors.

The source-only proof passes 120 paired Python processes and a separate guarded public registry write/read integration. It covers six independent neutral designs, 51 strict negative designs, one existing pre-read grammar rejection, the disclosed F14a initial/saved states and all four read-option modes. All audited phases use zero additional file access. The native-saved derivative's complete public result remains identical. There is no new native oracle, native-cache qualification, held-out credit or FCStd acceptance claim in this change.

[Construction and admission evidence](../../../../../../re/solidworks/records/SdkNoCachePrismRead2026.md) · [Process receipt](../../../../../../re/solidworks/measurements/2026/SdkNoCachePrismRead01.json) · [Native payload boundary](../../../../../Gotchas/Conversion/Solidworks/Archive/Partition/TypedPrismGeometryHasNoNativePayload.md)
