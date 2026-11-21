# Standalone constrained angular plane graph in SOLIDWORKS 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121, owner `/root/assembly_frontier`. This research composes an acute, unreversed plane constrained to an actual Right plane and a registered finite Top/Right hinge. The independent input is an ordinary origin plate with one blind boss, the datum and hinge names, the angle, the annotation view catalog, the selected leader, design intent and the modeled document clock. The starting revision is `49bd04792ee4e9505dbc5fdf7530cc185f42bdc6` with SDK source tree `144d69996547bb67bf12c7b8b7e48e3c5a8f9de6`. Pattern geometry, the seed merge and controlled native qualification remain open. [Composer](../../tooling/sw2026/linear_pattern/MakePatternAngularPlane.py) · [Measurement receipt](../measurements/2026/LocalLinearPatternAngularPlaneGraph01.json)

## Actual model relationships

| Owner | Rule and evidence |
| --- | --- |
| `moRefPlane_c.f6f8` | Retains `moConstraintCoincLineAtAnglePlaneRefplaneData_c` with its actual runtime plane owner. The base values follow the owner-taking constructor `0x4c2dadb0` and plane constructor `0x4c2d2d20`. The supported constrained subtype has mode 22 and the current ordinary selectors `f54=f58=-4`. Its frame, signed borders and name position follow the finite hinge and authored positive angle. |
| `f88.f08/f10/f18` | Ordered Right-plane angle, selected coincident hinge and a distinct coincident row with a null wrapper. The Right plane and hinge have their own local component selections. The line's first point, negative-Z direction and length come from the actual registered hinge. The local hinge orientation determines `f148=-3` in this profile. |
| `f150 → f850[0].o → ff0 → f28` | One `moDisplayAngularDim_c` owns one retaining `moFeatureDimHandle_c`, which points to one `AngleDim_c` and a private `moAngleParameter_c`. The real plane owns the data, display, handle, dimension and parameter during construction. Native constrained init `0x4b8ed160` creates the display with role 1 and the actual plane. The naming path `0x4c820f20` gives D1. `0x4c821c40` uses the shared persistent allocator for the dimension's `f50`. This consumes an identity before the plane's `f08` registration. The parameter's native constructor ID remains `-1`. |
| Angular driver and display placement | Authored radians drive the actual parameter and the copied scalar constraint. The display cache uses the documented one-element descriptor and packs its own modeled radians. The dimension stores the same three world witnesses and dimension-frame transform used to derive all 19 proved arc fields. Actual catalog membership allocates the `*Back` annotation ID and verifies its signed frame. Camera identity stays distinct. |
| Creation logs and allocation frontier | The same two generated headers publish the ordered model, hinge and plane creation records and the actual next persistent identity. Both freshly constructed features use the model's explicit creation event. The selected line's component reference joins the hinge's own creation row. The active CMgr configuration publishes the matching allocation progress. The two native source timestamps remain independently owned and are audited without using them as generation inputs. |

The four existing disclosed parts replay Config-0 and ResolvedFeatures exactly, with 24 roots and map counters `112 → 472`. Both source headers agree on the distinct hinge and plane creation events. The hinge is 41, the angle dimension is 44 and the plane is 45 in these sources. Those source counts and IDs are comparison evidence. Generation uses the normal allocators and current standalone model inventory. The runtime owner aliases are checked before serialization. The typed reader verifies their nested stream roles, local component identities, view membership, creation logs and parameter without fabricating unserialized pointers. [Constrained native initializer and roles](FreecadCylinderAngledPlanes2026.md#the-editable-driver-is-created-by-initialization) · [Hinge](LocalLinearPatternHingeAxisGraph2026.md) · [Arc](LocalLinearPatternAngularArc2026.md) · [View catalog](LocalLinearPatternAnnotationCatalog2026.md)

## Explicit leader input

`moDisplayDim_c::setForeshortenShiftedPoint` at `0x4c896990` stores its signed index at runtime `+0xf80` and its point at `+0xf68`. The ordinary angular display inherits the store at `0x4c82e7ef`, which writes the index through `su_CArchive::operator<<(long)`. The non-DB point store at `0x4c82e87a` consumes the same runtime point. The matching loads are at `0x4c830bd4` and `0x4c830be4`. The receipt pins the precise code and underlying imported archive overloads against SP05.2 build `34.5.2.0604`.

The narrow model requires an independently supplied angle-display index and an explicit zero shifted point. The angle's index is independent of the plate's automatically chosen display state. Three earlier disclosed indices are zero and the tall part records `16777215`, all with zero shifted points. These measurements supply no default. Each independently authored positive contrast changes the index from zero to one or one to zero. It yields a one-byte difference inside the actual display, with all other linked stream hashes and arc geometry equal. Native behaviour for either research-selected index has yet to be measured for the generated angular plane. [Shared constructor ledger](ProfileConstruction2026.md#live-dimension-construction-ledger)

## Guarded model verification

| Case | Plate dimensions (mm) | Angle | Annotation ID | Config-0 bytes | Resolved bytes | Final map |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| ArcGraphAlpha | 137.5 × 88.5 × 18.625 | 28.625° | 200 | 22800 | 18324 | 90 → 242 |
| ArcGraphBeta | 121.125 × 73.375 × 12.75 | 61.875° | 202 | 22986 | 18320 | 91 → 243 |

Four fresh processes independently build eight in-memory graphs from stdin with zero runtime file reads. Each model's two linked headers, CMgr, Config-0 and 21-root ResolvedFeatures section re-emit the generated bytes exactly. The prior 20 resolved roots match the standalone hinge prefix on the same Config map. Authored geometry independently predicts the angle, normal, witness centre and label radius. Six malformed inputs per graph fail before consuming a persistent identity, including a stale hinge-header access stamp. Five changed linked owners per graph fail strict readback.

The graph covers a standalone plate, hinge and constrained plane. The next pattern graph needs the independent raised seed profile, its merged body lineage, the live pattern owner and direction wrapper selecting this verified plane. Complete native container output, editable pattern qualification and held-out evidence remain pending. No SOLIDWORKS process ran for this comparison.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternAngularPlane.py \
  --binaries /absolute/licensed/module/directory \
  --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/AngularPlaneGraph.json"
```

## Shared construction

The shared archive constructor now owns the constrained plane, its live angle parameter, its view membership and its independently authored model annotation catalog. The ordered finite endpoints and real Right support determine the plane and display witnesses. The frame, transformed points and arc use the measured operation order. The angle, design-intent flag, shifted point and leader index are explicit inputs. The standalone part allocator computes the two actual persistent IDs in native registration order. Both headers and the active configuration retain the resulting identities and creation events.

The annotation catalog starts at the ordinary reserved identity. Authored order and right-handed cardinal bases determine the view rows and transforms. The active and shown assignments are explicit. The angle resolves the actual Back view independently of model cameras. The shared builder accepts the measured unreversed arc and catalog scope.

The annotation proof reproduces both authored outputs and six disclosed comparisons. The angular proof reproduces eight graphs and four disclosed prefix comparisons. The complete cache-free pattern proof reproduces the original, pitch-only and count-only files of both signed cases, including their six exact file hashes and twelve ordinary SDK reads. The earlier independent Windows acceptance applies to its frozen compiler closure. This change proves output parity on the disclosed files. Shared seed and pattern construction, public writer admission and broader geometries remain open. [Revision-bound receipt](../measurements/2026/SdkSharedAngularConstruction01.json)

Run the angular proof above, the [annotation catalog proof](LocalLinearPatternAnnotationCatalog2026.md), and the [cache-free pattern proof](SdkColdObliquePatternRead2026.md) from this checkout. Compare the standalone records after excluding only the tool provenance section and compare the full cache-free pattern result against the cold section of the portable angular datum receipt.
