# Linear pattern raised seed ownership in SOLIDWORKS 2026

The [guarded raised-seed receipt](../measurements/2026/LocalLinearPatternRaisedSeedGraph01.json) binds the source-only audit and the inputs and linked archives of two separately modeled Front-plane plate and seed pairs. The target build is SOLIDWORKS 2026 SP05.2, 34.5.2.0604. This is a research prerequisite for the bounded single-direction linear pattern from [the pattern ledger](LocalLinearPatternOwnership2026.md).

## Saved ownership

Six disclosed native saves reproduce their exact linked Config-0 and ResolvedFeatures bytes with the typed archive. The regular PlateBoss `moExtrusion_c` uses `f810=-1`. The later SeedBoss `moICE_c` uses `f810=0`, positive Front direction and a blind end with `f128=1`. Each `f818.f18` owns its own local display, handle, `ParallelPlaneDistanceDim_c` and D1 parameter. In these files the seed's `f530` aliases the actual plate result `f528`, and the pattern's `f530` aliases the actual seed result. These three atoms are also the actual manager objects. Their producer fields `f12c/f130` agree and their consumed states are `1,1,0`. The seed selector addresses the immediate plate atom and also names the original plate feature. The pattern selector names the same original producer and carries the seed atom followed by the plate atom. The two native-saved face references are distinct objects with an actual shared local external-reference owner.

The six linked source measurements demonstrate two orders of the same set of three atoms. In particular the independent spacing-edited save reverses the ordinary observed manager order. Source order does not establish a construction rule. Saved kernel tags change across the independent configurations and saves. The typed read checks these as saved provenance and never supplies them to the constructor.

## Fresh construction

[MakePatternSeed.py](../../tooling/sw2026/linear_pattern/MakePatternSeed.py) derives both `ThroughStock` rectangles from supplied extents, uses the shared ordinary Front profile, blind end and atom constructors, and binds the actual immediate atom to a local `moCompSolidBody_c`. It appends the new atom in producer order with the existing manager allocator. It retires only the actual live input. Depth and feature identifiers use the independent shared persistent allocator. Both headers record the actual generated plate and seed creation events from the supplied event instant. Independent two-shape analytic checks freeze a single body and eleven faces before adding any pattern instances.

The empty physical face slot is a cold construction proposal. The previously classified [one-body selector fast path](ThroughAllSelectedBodyConstruction2026.md) explains why the generic body feature resolver can select a sole current atom from its valid local wrapper and immediate ID without a saved face. This receipt does not establish that the native raised-seed and linear-pattern startup calls reach that branch. A true native open/rebuild/edit/save/reopen batch with fresh controls still has to establish that, separately from any later protected source qualification.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternSeed.py \
  --share /Users/odin/Documents/UniCAD/Oracle121Takeover \
  --output /tmp/<unused-directory>/LocalLinearPatternRaisedSeedGraph01.json
```

The outer process reads only the six hash-bound disclosures. Each of four isolated generation processes consumes a distinct modeled request from stdin, with two runs per request, and prohibits file reads after module import. All four produce and reciprocally validate CMgr, Config-0, both headers and ResolvedFeatures in memory. Their shared map counters are 90 and 221 and their 21 roots preserve four separately owned feature and profile identities. Six crossed or malformed owner variants and four infeasible raised-seed geometries refuse in each distinct modeled case. These are stream and graph measurements with zero native files written, native application launches or held-out credit.
