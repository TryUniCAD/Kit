# Ordinary revolved boss archive readback on SOLIDWORKS 2026

The three disclosed ordinary revolve sources round-trip byte-identically through the current archive grammar. Every required stream passed strict schema admission. The optional visual-state stream round-trips but reaches two provisional owners. Several saved construction values differ from author constructor state, so the archive result leaves specific writer obligations open.

## Bound discovery inputs

The source lock SHA-256 is `ece8557f66ac26e74d08085761d6afe474c9b12620a6c5b2703f2050ff2642d9`, source tool revision `5a9ec7b5ada121dbc437b5258a1cf216000b5eae`. The lock records 12 distinct processes, passing before and after controls, and a successful native driving-angle edit for each disclosed source, including the full turn. The oracle executable is SOLIDWORKS 2026 SP05.2 `34.5.2.0604`, SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Each native file and its author/reopen receipt hashes were independently checked against the lock. Readback used the three disclosed sources only.

| Source | Native bytes | Native SHA-256 | ResolvedFeatures bytes | Linked map base → final |
| --- | ---: | --- | ---: | --- |
| `RevolveFull` | 62796 | `28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0` | 12345 | 109 → 268 |
| `RevolvePartialForward` | 53529 | `0ea9ae68f7da6bd1d5542ce5b6689fd8f793dfcf2b5fefea44373043da17804d` | 12465 | 109 → 277 |
| `RevolvePartialReverse` | 54933 | `b3b345451717fef654043008f95f477a04cd369a1b838c86e7f7ef975080533b` | 12465 | 109 → 277 |

The archive grammar was read at Git revision `70d7a6ad1d4cf62130b779004e96e72c548a1a8d`, tree `ab5a190b2375298e91a35821f54b6a820a47839b`, using Python `3.13.15`. Both `RoundTrip.py --require-proven` invocations ran against the original native sources, first as independent streams and then with `--link-config`. Each source had 19 resolved roots, including one ordinary `moProfileFeature_c` and one `moRevolution_c`. The linked run loaded the complete Config-0 with map counter 109 and handed its state to the resolved stream.

| Run | Comparisons with identical bytes and no tails | Strict passes | Private report SHA-256 |
| --- | ---: | ---: | --- |
| Primary | 45/45 | 42/45 | `49d3cf65d2e3dabb11ceed460a1c7fcd9efcceced3c89ecbe34b272c1f8107ef` |
| Config-map linked | 45/45 | 42/45 | `48aaf3e1097514949a047d5af3c09f035fa7e98f49190ebea204ec33035363ea` |

The three strict failures in each run are solely `ThirdPtyStore/VisualStates` (1789 bytes per file). The two exercised provisionals are `moCompHolder_c` and `moDisplayedEntityTracker_c.Serialize`. No missing schemas were reached. `Contents/CMgr`, Config-0, ModelHeader, ResolvedFeatures, Definition, Biography, History and Header2 each passed in all three files and in both modes. The typed resolved and selected scope private receipts have SHA-256 `ab1c48e94a12e5d10cab990a0cf8f03138e63f7d6a512d0e4b18400b6f0db75d` and `d4630f31b4dc6afdfce5f689f4c480d24cc888c0ada6147ad07162eabc91705b` respectively.

Each primary comparison retained three fixed 16-byte operations in Config-0 (`moModel_c.FUN_4c22ec80.f784/f7a4` and `moSketchBlockMgr_c.f380`) and the fixed 8-byte `uiModelDoc_c.Serialize.clsid_d` operation in Definition. ResolvedFeatures retained one 8-byte operation at `moRevEndSpec_c.f18 → moDisplayAngularDim_c.f5b0 → dm.FUN_4bd03960.data`. This dynamic-array schema's raw operation represents a single reconstructible value here. The hash of the authored radians encoded as little-endian binary64 matches the saved payload in all three sources. The descriptor fields are `elem = 8`, `alloc_a = 16`, `alloc_b = 1`, and `n = 1`. This matches the common owned-display update recorded in the [dimension engine evidence](RadialStyleAndEngine2026.md), which replaces the cold zero element with the active parameter. Other unselected streams were outside these comparisons.

## Reconciliation with author construction

The native addresses below are for the [pinned constructor investigation](OrdinaryRevolvedBoss2026.md). Author-time probes and archive readback use distinct evidence. The three saves share profile object ID 26 and revolve ID 31 in this cohort. These are per-model persistent IDs. The exact saved links resolve through the linked configuration map.

| Field or object | Observed saved rule within the discovery scope | Classification and remaining proof |
| --- | --- | --- |
| `moRevolution_c.f60` | One dependency resolving to the same ordinary profile that owns the selected line. | Derived ownership. Use the authored graph, not numeric IDs from a source. |
| Feature `f808/f810`, `f8d8` | Legacy displays null, modern `moRevEndSpec_c` present. | Confirmed modern branch in these three sources. Constructor `0x4c38aa40` uses that branch when the final argument is zero and the pinned gate returns one. |
| Feature `f824` | `0`, `0`, `1` for full, partial forward and partial reverse. | Direct direction input. The direction-only pair changes this field and preserves the positive angular parameter. |
| Feature `f820` | `0` for all three. | Confirmed saved private one-direction type for both angle regimes here. The reopened public API `Type` is also `0` in all three. `360°` alone does not select a different archive type in this protocol. |
| Feature `f818` | Present `suObList` with zero items in all three. | Null at constructor `0x4c38ac4d`; becomes a present empty list before save. Find the list producer or storage normalization and its condition. |
| Feature `f828/f870/f8e8` | `3/1/0` in all three. | Matches constructor assignments. Full field meaning and wider domains remain open. |
| End flags, end refs and distances | `f08 = 1`, `f138/f13c/f0c/f10/f140/f144 = 0`, no target point or wrapper references, `f38/f40 = 0.01 m`. | Matches one-direction blind flags and inactive constructor offset defaults. The author API supplied zero inactive offsets, separating it from the observed `0.01 m` rule. Semantics of `f138/f13c` remain open outside this mode. |
| End `f18/f20/f28/f30` | Present angular display in `f18`, other three null. | The constructor creates both angle displays. The saved owner lifecycle retains only the active forward display in this mode. Trace forward/reverse display removal or serialization gating. |
| Angular value | `moDisplayAngularDim_c` owns `moFeatureDimHandle_c`, `AngleDim_c`, and `moAngleParameter_c`, with `moAngleParameter_c.f58 = 6.283185307179586` or `1.9722220547535925` radians for full or partial. | Direct positive angle input, consistent with edited native feature and source. Partial `moDisplayAngularDim_c.fad0` is `0.0016677716441343365` and cannot serve as the angle. The full-turn cache happens to equal the angle. |
| Angle placement | The direction-only pair keeps the authored positive angle and both end direction vectors in the dimension's local frame. `AngleDim_c.ff0` changes the frame orientation and axial translation sign. The full-turn display's `f1018` is `0x1b`; the partial pair uses `0x18`. | Presentation frame, cache values and mode flags require constructor/UI derivations or an independently proven neutral state. |

## Selected axis and local component identity

`moLineRef_w.f58` owns `moCompSketchEntHandle_c`, whose component is `moUnitComponent_c`. Its live line reference `f0f8` is `sgLineHandle` with `idx = 5`, `f1c = -1`, `f08 = 0`. The index resolves to the sixth row in the authored sketch's six native line slots. The two line endpoints at point indices 8 and 9 have the requested coordinates. The axis line's row `flags = 2` and entity `f54 = 0x000c` separate it from the four perimeter lines with row flags `0` and entity `f54 = 0x0004`. The extra native row at index 0 is outside the four requested perimeter entities and selected axis. The serialized slot and point counts must reflect the full generated sketch graph. The class getter and setter binding for centerline mask `0x8` is recorded in the constructor study. The meaning and initialization of row `flags = 2` remain to be traced.

The component sketch handle's `ff0.f00` resolves to the profile's persistent ID. Its `ff0.f08` varies across native saves and its source still needs a pinned setter trace. `f100 = 1`, whereas the traced generic component sketch handle constructor initializes it to zero. Its authoring/save mutation and any conditions on the flag remain open. The wrapper records `f68 = 1`, `f08 = 118`, `f0c = 0`, `f70 = 19000`, null component override `f60`, and absent transform records. `f08` and `f0c` differ from the traced wrapper constructor, which starts `101` and `-1` respectively. These are observed saved states until the actual local-selection initialization path is recovered.

The saved geometry values are `fc8 = P0` in model coordinates, `fe0 = normalize(P1 - P0)`, `fb0 = 0`, and `fb8 = dot(P1 - P0, fe0)`. The measured spans are `0.063 m` and `0.054 m` for the full and partial families. Reversal leaves the selected line data unchanged. The validated axis geometry uses the finite endpoints of the authored line. The native resolver at `0x4c316200` supports the endpoint and projection derivation, and the disclosed saves confirm the caches are populated before writing. Wrapper `ff8` is zero here.

## KeyWords framing and current writer boundary

All three `swXmlContents/KeyWords` streams are 1667 bytes. Their framing is `0x86`, the UTF-8 XML declaration and CRLF, the document XML, and a final CRLF. ElementTree parsing followed by re-emission with native `/>` spelling for empty elements gives exact bytes in all three. Standard ElementTree inserts a space before `/>`, causing the first difference at byte 186. This comparison is separate from `RoundTrip.py`'s modeled stream count.

The feature is `<Feature Type="Revolve">`, with `D1` text `360°` or `113°` in presentation units. Its sketch appears as `<Sketch>` with `Dissectable="true"` and no `Type` attribute. The metadata builder at the readback revision emits a `Type` for every generated feature tag, accepts only numeric dimension text, and uses ElementTree's spaced empty markers. The native angular and consumed sketch form are separate generation rules.

The [generated candidate ledger](OrdinaryRevolvedBossConstruction2026.md) records subsequent tracing of `f818`, line slot flags and the permanent mark, together with the remaining wrapper, active-angle and presentation questions. The optional visual-state provisionals have a separate strict-admission outcome. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) require independent generator and held-out acceptance.
