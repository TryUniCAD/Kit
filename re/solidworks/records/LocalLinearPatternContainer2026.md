# Model-only container for a bounded SOLIDWORKS 2026 oblique linear pattern

Task `B04-SW2026-LOCAL-LINEAR-PATTERN` in PR #121. The [model-only container receipt](../measurements/2026/LocalLinearPatternContainer01.json) records two independent generated designs, one pitch and one count contrast for each, and four previously disclosed native source replays. The target is SOLIDWORKS 2026 SP05.2, 34.5.2.0604. This is the first complete research container for the local raised-seed, finite hinge and oblique direction combination. Native acceptance of the containers is pending.

## Construction and owners

[The independent raised-seed proof](LocalLinearPatternRaisedSeed2026.md) supplies the origin Front plate and the interior Front seed as separate blind profiles with separately editable D1 lengths. The seed joins the sole live plate body. The [hinge and direction construction](LocalLinearPatternDatumBorders2026.md) supplies the actual Top and Right parents, through-origin finite axis, angle constraint and its distinct D1. Creation identities for the hinge and plane come from the actual allocator and both header creation logs.

The native owner-taking `moLPattern_c` constructor at `0x4bfbb9d0` calls the owner-taking inherited constructor at `0x4c0423d0` and the line/dimension factory at `0x4bfe62b0`. The factory constructs six different displays in slot order `f1258/f1260/f1268/f1270/f1318/f1320` with parameter ordinals D1, D3, D2, D4, D5 and D6. The first and third are integer-parameter owners. The other four are length-parameter owners. The optional dimension-reference inputs and second line are absent in the admitted single-direction mode. The base original-dimension holders are separate empty constructor-owned states. Their typed restore rules are already recorded in [the archive layout record](LocalLinearPatternTypedArchive2026.md).

[MakeLocalPattern.py](../../tooling/sw2026/linear_pattern/MakeLocalPattern.py) binds the actual `moICE_c` seed at `f988`. It retires the actual immediate seed result and allocates the final managed atom. The local wrapper `f548` selects the seed result at `f18/f1c`, points to the actual original plate producer at `f108`, and carries the immediate and base atom IDs in that order at `f110`. The orphaned result and copied historical face branches are excluded. The actual native pattern regeneration path calls `moAtomFeature_c::getPartBodiesForFeatureRegen` at `0x4c045ddd` with options 0/0 when the active scope and empty runtime marker reach that call. The [previously classified sole-stock branch](ThroughAllSelectedBodyConstruction2026.md) can resolve from the actual positive atom and local wrapper. Native first-open verification is still needed for this selector with an absent historical face.

The first frozen pattern candidates started with the owner-taking constructor's `f9f0=0` and `f1054=0`. The [direct parent investigation](LocalLinearPatternParentScope2026.md) identified the extra plate dependency and corrected `f9f0` for verified single-stock scope. The first byte is also updated by regeneration on branches with real current-body and scope evidence, including a body comparison at `0x4c045eaa` and the guarded wrapper-ID path at `0x4c046246`. The latter has additional runtime `f4d0` and `f544` gates. The second belongs to the appearance application path, including reads and writes within `moPattern_c::applyVisProp`. Its previous native-saved value of one is not an initial rule. The model supplies the ordinary inherited propagate-visual setting without custom appearance associations. The receipt binds these native boundaries by hash.

The `f1288` local line is constructed from the actual angular plane, an exclusive local component, its persistent identifier and the matching creation event. `f100=0` identifies this constructed plane role. The [measured resolver arithmetic](LocalLinearPatternDatumPlacement2026.md) uses its finite display rectangle for the point and unit direction. The separate `f1298` polarity reverses travel and does not rewrite the selected plane frame. The largest proposed supported count is eight, with a positive pitch and strictly separated raised footprints wholly within the original plate.

## Live values and drawing state

The live integer count is D1 and the live length is D3 in metres. The dormant second count's parameter is one and its display cache is zero. The other dormant length parameters and caches are zero. Parameters, dimensions, displays and handles are distinct vertices. Only the six addressed dimensions use the shared persistent model allocator. The active display IDs use the separate model `fd44` allocation in D3 then D1 order. Four disclosed oblique source replays independently show actual display IDs 11 and 10 in D1 then D3 order, with model frontier 12.

The count display joins its actual `*Back` annotation frame, and the pitch has the ordinary unassigned ID 199. This differs from the previously studied principal directions with named pitch annotation views. The actual model's `ReadModelLinear` projection supplies the distance presentation fields independently of the integer-display defaults. All six display text anchor and leader inputs are explicit. The active distance text uses zero anchor and the supported midpoint mode only. D3 model witnesses come from the constructed seed minimum Front corner and its signed translation by one pitch. Four independent authored source cases, including the large pitch edit and both seed heights, corroborate those witness locations within (10^{-15}) m. Display distances and the binary64 cached parameter follow their distinct geometric and live-value owners.

[EmitLocalPattern.py](../../tooling/sw2026/linear_pattern/EmitLocalPattern.py) uses the shared complete part emitter for the document, configuration, history, model Definition and metadata and the tabulated research codec for the complete linked Resolved graph. Both stock profiles, both stock operations, hinge, angle and pattern receive actual feature rows. The Keywords pattern row exposes D1 and D3 only, and the angle row uses the degree suffix from the actual angular driver. The SDK builds the version-4 container from ten modeled streams. The cold output carries no imported body, Parasolid partition, borrowed reference row, recorded bytes or native-source template. Its rule-derived direction and parametric body history still require SOLIDWORKS to evaluate the model.

## Reproduction and boundaries

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProveLocalPatternContainer.py \
  --share /Users/odin/Documents/UniCAD/Oracle121Takeover \
  --binaries /Users/odin/Documents/UniCAD/Sw2026Research01a1dc84/bin \
  --output /tmp/<unused-directory>/LocalLinearPatternContainer01.json \
  --candidate-directory /tmp/<empty-owned-directory>
```

The supervisor reads the four disclosed, individually pinned source paths and the licensed build-matched module to report evidence. Each isolated author receives only its modeled JSON on stdin. Ten fresh author processes generated six independent states, repeated both original receipts and verified both original binary transports. Every state had nine byte-exact typed stream replays, ten container payload streams and 24 linked feature roots. Five invalid model inputs and nine malformed provenance, selection or driver owners were refused per state. Neither runtime file access nor CAD invocation occurred. Each independent same-locator pitch or count edit changes precisely ResolvedFeatures and Keywords, leaving the rest of the serialized graph and allocated identities exact.

The two frozen originals encode `C:\KitGeneratedLocalPattern\ColdRaisedPatternA.SLDPRT` and `C:\KitGeneratedLocalPattern\ColdRaisedPatternB.SLDPRT`. Independent solid-cell integration predicts one body and 21 or 26 faces, respectively. The smallest native comparison edits only D3, from 18 to 24 mm and 19 to 22 mm respectively. The signed direction and count remain the same, with a distinct centre of mass and exact independent expectations for the unchanged volume, area and extents in each case. The original and edited per-case observations, exact input and stream digests, semantic driver names and physical predictions are in the receipt.

A clean restart, document and rebuild diagnostics, the actual native feature and dependency order, local D1/D3 editability, clean save and fresh reopen with healthy bracketing controls must be observed on the pinned build. Native-generated default tree, annotation refresh and source-only presentation differences require their own observations. The two pre-writer protected sources remain unopened for this work. This construction has zero native lifecycle or held-out credit and does not activate the public reader/writer for this oblique profile.

## First disclosed native comparison

Both exact generated originals opened at their encoded locators with zero
errors and warnings. Independent cold and rebuilt geometry agrees with one
solid and 21 or 26 faces. Volume, area and centre of mass match the frozen
predictions. Both live pattern parameters and the actual seed and direction
selections match. The two known controls also pass.

The strict observer fails the dependency selection check in both cases.
The generated feature exposes three native parent features, the plate,
the raised seed and the direction datum. The independently authored
native products expose two, the raised seed and the direction datum.
The first run stopped on this dependency mismatch before the pitch edits.
[Observer](../../tooling/sw2026/linear_pattern/ObserveGeneratedLinearPattern.py) ·
[Strict native result](../measurements/2026/GeneratedObliquePatternNative01.json)

The [single-stock correction](LocalLinearPatternParentScope2026.md)
preserves both body atoms and generates the native direct-parent flag
from their verified scope. Both corrected files pass the same strict
observer across cold open, rebuild, D3 edit, save and fresh reopen.
[Corrected native result](../measurements/2026/GeneratedObliquePatternNative02.json)

## Shared dimension construction

The shared archive constructor now creates all six dimensions, display owners and handles. It verifies the local pattern owner and its separate integer and length factories before it calls the common display initializer. Active D3 and D1 take the next model display IDs in that order. All six dimension IDs follow the persistent allocation order. The actual Back view supplies the count membership. The reserved unassigned view supplies the pitch membership. Native document style supplies the distance projection. Each cache derives from its own parameter and active display assignment.

The [complete container comparison](../../tooling/sw2026/linear_pattern/ProveLocalPatternContainer.py) and [cold SDK comparison](../../tooling/sw2026/linear_pattern/ProveColdPatternRead.py) retain all six corrected file hashes, four linked native input comparisons, the two-stream edit boundary and all twelve strict path and stream reads. A separate older neutral writer proof remains pinned to its original compiler and source tree. No new native process or protected file participated in this refactor. [Shared constructor evidence](../measurements/2026/SdkSharedPatternDrivers01.json)

## Shared complete archive

The ordinary part composer now consumes the shared portable planner's typed input. Actual stock, seed, hinge and constrained plane owners determine the supported direction and local selector. The seed footprint repeats at the signed pitch. The constructor checks that every footprint is strictly inside the plate and remains separated from every other footprint. The inherited pattern constructor creates its own independent original-dimension holders. The two drivers and their inactive companions allocate before the pattern owner. The actual joined seed and its original plate drive the last scope wrapper and result atom.

The shared archive emitter writes all ten part streams and their normal compound container. The linked feature rows keep the actual stock prefix and append only the axis, plane and pattern. The shared Keywords composer writes its measured lexical feature groups and actual live owners, including the single D1 in degrees on the constrained plane. The cache-free part uses the generative feature graph for its one solid.

The current proof passes both previously native-tested disclosed original files and four isolated pitch or count edits through normal neutral JSON, the shared planner and the shared composer. All six complete file digests and all 60 stream digests match. Each new generation replays nine typed streams exactly. A seventh process refuses an overhanging footprint before archive emission. The separate cold regression reproduces all twelve SDK path and stream reads and both signed cases. The private held-out writer closure and the public registry route still require explicit verification. [Complete emission receipt](../measurements/2026/SdkSharedPatternEmission01.json)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/neutral/ProveSharedPatternEmission.py \
  --disclosed /absolute/share/Oracle121Takeover/GeneratedLocalPatternNative02 \
  --output /absolute/unused/SharedEmission.json
```
