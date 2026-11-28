# Linear pattern raised seed ownership in SOLIDWORKS 2026

The [guarded raised-seed receipt](../measurements/2026/LocalLinearPatternRaisedSeedGraph01.json) binds the source-only audit and the inputs and linked archives of two separately modeled Front-plane plate and seed pairs. The target build is SOLIDWORKS 2026 SP05.2, 34.5.2.0604. This is a research prerequisite for the bounded single-direction linear pattern from [the pattern ledger](LocalLinearPatternOwnership2026.md).

## Saved ownership

Six disclosed native saves reproduce their exact linked Config-0 and ResolvedFeatures bytes with the typed archive. The regular PlateBoss `moExtrusion_c` uses `f810=-1`. The later SeedBoss `moICE_c` uses `f810=0`, positive Front direction and a blind end with `f128=1`. Each `f818.f18` owns its own local display, handle, `ParallelPlaneDistanceDim_c` and D1 parameter. In these files the seed's `f530` aliases the actual plate result `f528`, and the pattern's `f530` aliases the actual seed result. These three atoms are also the actual manager objects. Their producer fields `f12c/f130` agree and their consumed states are `1,1,0`. The seed selector addresses the immediate plate atom and also names the original plate feature. The pattern selector names the same original producer and carries the seed atom followed by the plate atom. The two native-saved face references are distinct objects with an actual shared local external-reference owner.

The six linked source measurements demonstrate two orders of the same set of three atoms. In particular the independent spacing-edited save reverses the ordinary observed manager order. Source order does not establish a construction rule. Saved kernel tags change across the independent configurations and saves. The typed read checks these as saved provenance and never supplies them to the constructor.

## Fresh construction

[MakePatternSeed.py](../../tooling/sw2026/linear_pattern/MakePatternSeed.py) derives both `ThroughStock` rectangles from supplied extents, uses the shared ordinary Front profile, blind end and atom constructors, and binds the actual immediate atom to a local `moCompSolidBody_c`. It appends the new atom in producer order with the existing manager allocator. It retires only the actual live input. Depth and feature identifiers use the independent shared persistent allocator. Both headers record the actual generated plate and seed creation events from the supplied event instant. Independent two-shape analytic checks freeze a single body and eleven faces before adding any pattern instances.

The initial stream proof used the empty physical face slot as a cold construction proposal. The previously classified [one-body selector fast path](ThroughAllSelectedBodyConstruction2026.md) explains why the generic body feature resolver can select a sole current atom from its valid local wrapper and immediate ID without a saved face. The later [disclosed native comparison](../measurements/2026/GeneratedObliquePatternNative02.json) measured the two complete oblique pattern candidates through open, rebuild, edit, save and fresh reopen. The [separate locked-source comparison](LocalLinearPatternHeldoutEvaluation2026.md) measured the earlier complete compiler on two independently authored sources.

## Shared constructor

The internal [stock constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Stock/MakePatternSeed.py) takes the part name, configuration, output path, event time and two bounded Front-plane boxes. The plate starts at the model origin. The seed starts on the same plane, lies strictly inside the plate footprint and rises above the stock. Both boxes retain finite extents, distinct sketch and feature names and their own blind D1. The [research entry](../../tooling/sw2026/linear_pattern/MakePatternSeed.py) delegates to that constructor and retains its existing input and result attributes.

The shared body binder checks the concrete plate and seed producers, actual feature output arrays, ordered manager membership and consecutive allocated atom IDs before selecting the immediate live result. The one later pattern uses the same binder after it verifies that the seed previously consumed the actual plate. Each atom's two producer IDs refer to its own feature. The wrapper carries the immediate result and the base producer's lineage while its physical face slot stays empty. The stock graph retains the common persistent allocator. Both model headers append creation rows for the actual allocated feature IDs using the supplied event time, then the existing renderer emits the graph.

The prototype at aggregate `f0ec26e293a20ed6ecb1d2834b994bafe6956b70` and the shared constructor replay the same two modeled graphs and all six disclosed saves. The five modeled streams per design, the 21 ordered roots, map counters 90 and 221, managed IDs 101 and 102, consumed states 1 and 0, all twelve reader ownership refusals and all eight geometry refusals match. The seed report SHA-256 is `20a5984779b87a00b7eb536df0c3db06ea97f0f7cd70e9017b71e013aa0c15c6`; only the compatibility script digest differs from the prototype report. The [existing guarded model container process](../../tooling/sw2026/linear_pattern/ProveLocalPatternContainer.py) also reproduces both complete disclosed candidate bytes and each independent pitch and count variant. The complete model report SHA-256 is `0f9dee4216c558c00c84f8791b0038a3b674f054dfe14080a85fb480446d9d98` before and after extraction.

| Disclosed complete candidate | Bytes | SHA-256 matching the earlier native result |
| --- | ---: | --- |
| ColdRaisedPatternA | 10,474 | `f7e5290dfda2cd2aedfc281ea8ee6275fd1214fc011bcda51f88d43d8cc4356f` |
| ColdRaisedPatternB | 10,461 | `032c9c5696a4b97a9a5c5178147cb8443b90a6350588154dec693ff56d372754` |

A guarded writer contrast refused a reordered manager, a crossed result, a retired immediate atom, a seed that consumed the new result, and a cached kernel tag before changing the selection fields. An additional check refused a duplicate header creation owner and a nonfinite seed box. The generation processes attempted zero runtime input reads. Later annotation and pattern drivers still use their existing owners. This extraction has no new native or held-out runs, public admission or broader shape support.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternSeed.py \
  --share /Users/odin/Documents/UniCAD/Oracle121Takeover \
  --output /tmp/<unused-directory>/LocalLinearPatternRaisedSeedGraph01.json
```

The outer process reads only the six hash-bound disclosures. Each of four isolated generation processes consumes a distinct modeled request from stdin, with two runs per request, and prohibits file reads after module import. All four produce and reciprocally validate CMgr, Config-0, both headers and ResolvedFeatures in memory. Their shared map counters are 90 and 221 and their 21 roots preserve four separately owned feature and profile identities. Six crossed or malformed owner variants and four infeasible raised-seed geometries refuse in each distinct modeled case. These are stream and graph measurements with zero native files written, native application launches or held-out credit.
