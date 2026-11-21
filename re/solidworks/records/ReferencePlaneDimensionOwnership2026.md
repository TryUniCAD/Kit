# Offset-plane source dimension ownership

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. This record covers the first disclosed source-author failure and a separately frozen observer retry. Root owns the VM, Git and shared registers. [Original source protocol](ReferencePlaneConstruction2026.md); [managed construction rules](ReferencePlaneManagedConstruction2026.md).

## Measured first attempt

Packet `9aad0b09e29433e61d0be577667fba399ca0d52310835b20b2bccff52c7afd08` remains immutable. The metadata preflight passed without starting a CAD process: both registered libraries were `34.0`, the six-argument `InsertRefPlane` binding matched, indexed properties were DISPIDs `17/18/19`, and the explicit plane transform property was DISPID `3`. Metadata receipt SHA-256 `fb37d7dcde62d33b33564fa4fddba6f9c37ffbf3f681e70bd0bd4925e917b010`.

The first disclosed `D01` author phase then failed before its first native save. Its raw receipt SHA-256 is `2dc9377ba402d9a2efa8fbda1f14bbd2f4f8dfad2f5be6a2ea55198903c1ed87`. Independent original controls before and after passed open/rebuild at `0/0`, with no native dialog or controller diagnostic. There were three distinct native processes. [Sanitized receipt](../measurements/2026/ReferencePlaneDimensionOwnershipRetry01.json), SHA-256 `04b43dfa9b305fe66ed715fa64ef246cd02815f8b02be09c5ae8dcf04e5196bb`.

The trace binds these observations separately:

| Observation | Result |
| --- | --- |
| Circle creation's driving dimension | `D1@Sketch1@Part1.Part`, `0.00831 m`, driving state `2`; setter returned `0` |
| Profile feature identity during creation | The sole `ProfileFeature` was renamed `PlaneSketch` and selected for the boss |
| Selected plane constraint | First index `0`, distance code `8`, value `0.01379 m`; parent `Front Plane`; API `Type=5`, `Type2=11` |
| Sketch world frame | Origin `(0,0,0.01379) m`, normal `(0,0,1)` |
| Native body | One solid; volume `1.4036415028027867e-6 m³`, area `0.0007717121291613496 m²`, centroid approximately `(0,0,0.017025) m` |
| Independent cylinder prediction | `πr²d`, `2πr(r+d)` and plane origin plus `(0,0,d/2)` matched to six significant figures |
| Rebuild state before failure | `GetWhatsWrongCount=0`, `NeedsRebuild2=0` |
| Later radius observation | `GetFirstDisplayDimension` → `GetDimension2(0)` → `SystemValue` produced `0.01379 m`, immediately after the plane's first-display query |
| Failed display's actual parameter identity | **Not recorded**: neither `FullName` nor native/canonical object identity was checked for that returned dimension |

The later value equals the plane distance and disagrees with the correctly authored circle radius. That establishes a failed radius observation, not its precise dispatch or ownership cause. A cached proxy, a traversal starting point and an unexpected native feature binding remain distinguishable hypotheses. This record does not label any of them as a confirmed vendor or pywin32 defect. No native source sibling was saved, no source lock qualified and no hidden design was exposed by this attempt.

## Frozen retry

Packet `c8adf64a7c6d44bc0cc9df66b7526dc4d1f49028ec2840888201f3ae298a99c0` is a new packet. The disclosed specification and native control are byte-identical to packet 01. The original packet, its tools and raw receipts were not edited. Geometry, scalar inputs, tolerances and the required native author/edit/save/reopen checks are unchanged.

[ReferencePlaneDimensions.py](../../tooling/sw2026/ReferencePlaneDimensions.py) adds explicit ownership observations. It resolves members from the registered pinned interfaces and performs fresh `IDispatch::Invoke` calls with their declared DISPIDs and invocation kinds. It verifies each feature's actual name and kind, reads `D1@OffsetPlane` or `D1@PlaneSketch` through the model's named parameter API, checks that parameter's full owner name, driving state and editable state, and traverses the named feature's displays with a bound of twelve. A returned first display alone does not identify the requested parameter. Exactly one traversed display must match the named parameter, carry the correct physical dimension kind and bind the same native dimension object.

Native object comparison uses the registered `ISldWorks.IsSame` method and records canonical `IUnknown` equality independently. A native `swObjectSame` passes. `swObjectUnsupported` passes only when the canonical COM identity is equal; `swObjectNotSame` fails. The registered values are checked against the official [2026 object-equality enumeration](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swObjectEquality.html): `0`, `1`, `2` for not same, same and unsupported. This is an explicit identity rule, not a numeric-value fallback.

During authoring, the named radius parameter is also compared with the actual dimension returned at creation. Reopen uses the fresh named parameter and display binding. An independent ordinary-circle query checks the actual arc radius in metres, local center and segment identity. The existing independent whole-body geometry and support-transform checks remain mandatory.

The expanded metadata-only preflight must bind `IFeature`, `IDimension`, `IDisplayDimension`, `ISldWorks`, their selected members, `swObjectEquality` and `swDimensionType_e` before CAD activation. Metadata 01 did not inspect those extra bindings. A missing declaration, different physical type, wrong native owner or absent matching display fails the retry. No observer success is assumed before the new native run.

## Frozen identities and procedure

| Tool | SHA-256 |
| --- | --- |
| `AuthorReferencePlaneSources.py` | `a2df6c81c6f8366cd5da14fefa685c279ef26f2c4271c6536e0afff71593c6aa` |
| `ReferencePlaneDimensions.py` | `ada024b7a43428ca599ad14356adaeb4080b273559ea6214393691135f370504` |
| `ReferencePlaneSourcePhase.py` | `67792e517b979a9d48c37a1870c3f8bb889868c386b5f65c5e831461d7c08aff` |

The private transport recipe is SHA-256 `d844c99881e6d268758d2def8b6c0747a1d8e7a2215c39036e224d953ecfa0e0`. Its Windows arguments were checked to have canonical single separators after the drive/UNC prefix. The full public packet and tool identities are also bound in the sanitized receipt.

Root first commits the source tranche, verifies the frozen packet and runs `D00 metadata`. Inspect the new signatures and enums before `D00 before` and `D01 author`. Continue the original disclosed sequence only if each dependency passes; always run the trailing control independently after a failure. A complete healthy disclosed cohort is still required before guest-only hidden source generation. No writer begins before the independent source locks qualify.

Offline verification: all three changed/new Python tools parsed, the freezer's independent process verifier returned `0`, the disclosed specification/control comparison was byte-identical and the original frozen author hash remained unchanged. The first failure's native controls, geometry and exact records were independently reread. The retry's native metadata, author, edit, persistence and reopen remain unexecuted in this record. A cause-specific gotcha requires the retry's actual parameter/feature identity evidence.

## Qualified first disclosed source after transport retries

The preparation state above is preserved as history. Packet 02 passed its expanded metadata check, but its `D01` author transport exited `255` before any guest author progress or output. The independently run trailing control passed; this is not a native source failure. Freshly rooted packet 03 retained all fourteen tool bytes, disclosed inputs and native control. Only the share/output custody and fixed private directory changed. Packet 03 SHA-256 is `c05c429097c4ad94177afd3cddd9535ca373a31e6dcfa845375d9c09c96d2e89`.

Its leading control, `D01` author, fresh reopen and trailing control all passed in four distinct ordered native processes. Both native saves returned `[true,0,0]`; both saved siblings freshly opened at `0/0`, rebuilt with clean trees and retained editable parameters. [Native source receipt](../measurements/2026/ReferencePlaneSourceD01Native01.json), SHA-256 `50dd331f9ad3a4bfd1fcaea02655203dc62ea8872050abd3d2857a7e5c7072fa`.

The corrected observer measured the actual ownership cause. For the verified `PlaneSketch` feature, explicit native display traversal starts with `D1@OffsetPlane` (linear display type `2`) and then returns `D1@PlaneSketch` (radial display type `5`). The named radius, creation dimension and matching display compare `IsSame=1` with equal canonical `IUnknown`; fresh feature lookup also compares equal. The circle's actual radius is `8.31 mm` and center is local zero. This confirms the first-display ownership assumption was wrong in this profile; it does not establish a stale-dispatch defect. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/SketchDisplaysCanIncludeSupportPlaneDimensions.md).

The original plane distance is `13.79 mm`, edited to `24.53 mm`; radius stays `8.31 mm`, blind depth `6.47 mm`. Volume remains `1.4036415028027867e-6 m³` and area `0.0007717121291613496 m²` to six significant figures. Centroid Z moves from `17.025 mm` to `27.765 mm`, exactly the declared `10.74 mm` plane-distance change. Both fresh-read siblings retain those values, one solid, clean feature trees and the same support relation. Native `.x_t` and `.step` exports also returned `[true,0,0]`.

Typed readback reaches complete six-stream byte identity and continuous Config/Resolved map re-emission, then the first frozen source-audit projection correctly rejects the measured compatibility owner. Both saves persist `moFaceRefPlnData_c`, `moDisplayDistanceDim_c` → `moFeatureDimHandle_c` → `ParallelPlaneDistanceDim_c` → `moLengthParameter_c`, whose parameter/display distance changes from `0.01379` to `0.02453 m`. API `Type2=11` therefore does not imply the persisted constrained-plane owner in this single-reference case. The [managed compatibility path](ReferencePlaneManagedConstruction2026.md) already constructs this face-plane owner; further typed projection is readback work, not permission to emit captured values.

This is one qualified native-authored disclosed Front profile. It is not generated output, a complete source cohort, a hidden source lock or family writer acceptance. Packet 03's tail bracket is closed. A byte-identical freshly rooted packet 04 (`db56b95bad3543b5949848ce263bc8865c578ead20b688166d0b576310eeda7a`) supplies the complete four-case source sequence and later guest-only locks; cases run after packet 03's tail cannot borrow that earlier tail control.
