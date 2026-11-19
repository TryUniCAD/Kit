# Directed hinges and the ordinary oblique-cylinder angle sign

Task `B04-SW2026-FREECAD-CYLINDER`, owner `assembly_occurrence`, delivery PR #121. This source-only tranche pins the ordinary angle/line sign and prepares two separate disclosed authoring probes. It does not implement a writer or qualify an oblique cylinder. The exit condition remains independently locked native sources, a source-preserving generative feature chain, and controlled native open/edit/rebuild/save/reopen against unseen inputs. The missing FreeCAD full-property and target-history qualifications remain open.

Dependencies are the [public angle call](FreecadCylinderAngleApi2026.md), [concrete angled-plane owners](FreecadCylinderAngledPlanes2026.md), [persistent selected direction](FreecadCylinderDirectionWire2026.md), and the separately frozen [typed COM-output repair](FreecadObliqueCylinderObserverRetry2026.md). This tranche preserves both earlier source packets and their original expectations.

## Exact-build rule

The [reproducible pin](FreecadObliqueCylinderSign2026.json) binds 16 complete native functions, 6,821 code bytes, the two relevant concrete virtual slots, three actual imports and the original sign-mask span. It binds `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` and `sldmgu.dll` SHA-256 `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c`. Vendor modules and disassembly stay outside the checkout.

| Boundary                   | Exact original route                                                                                      | Independently authored rule                                                                                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Two-plane axis constructor | `sldmodu:0x4c281520`                                                                                      | Retains the two actual plane wrappers, first at `f80`, second at `f88`; it does not reorder them                                                                                     |
| Axis calculation           | `moPlaneInterAxisData_c` vtable `0x4d162258`, slot `+0x90`, target `0x4c286ca0`                           | Resolves those planes in order and supplies them to the actual `interLine` import at IAT `0x4cd3c030`                                                                                |
| Plane intersection         | `sldmgu:0x31e0bd50`, cross helper `0x31f1a050`                                                            | Direction is `normalize(n_first × n_second)`; the cross helper implements the ordinary signed coordinate cross product                                                               |
| Angular value              | `sldmodu:0x4b8ee700`, scalar getters `0x4b2bd110` and `0x4b2b1c70`                                        | Reads actual angle geometry `f38` and reverse byte `f40`; reverse negates the angle through the pinned sign mask                                                                     |
| Perpendicular plane/hinge  | `0x4b8eea56` through `0x4b8eeb04`                                                                         | Projects the plane normal perpendicular to the actual directed line, normalizes it, rotates it about that line with the signed angle, and retains the resulting normal at data `ff0` |
| Native rotation            | Import `mg_RotateXform`, `sldmgu:0x31f24670` → `0x31e2cd80`; vector transform `0x31f19400` → `0x31f1a0d0` | Ordinary nonzero rotation is the right-handed Rodrigues rotation about the supplied directed line; native row-vector matrix storage does not reverse this geometric convention       |
| Publication                | Concrete virtual `+0x238 → 0x4b8e8dd0`, plane construction `0x4b8ef160`                                   | Uses the completed real normal and the actual line point to make the plane; it does not replace the reference by a calculated anonymous direction                                    |

The skew line/plane branch preceding `0x4b8eea56`, near-zero and parallel degeneracies, projected lines, multi-plane counts, foreign component frames and old-API compatibility construction remain separate. This record does not admit them.

For a real unit hinge `u`, base normal `n` and desired normal `m`, the independently calculated rotation is `atan2(u·(n×m), n·m)`. Supply the positive magnitude to `InsertRefPlane`, and set mask bit `256` when that rotation is negative. The actual perpendicular-hinge and acute-angle checks are mandatory. A positive scalar alone does not choose the physical source tilt.

## Preserved disclosed failure

The only native data inspected here is the original failed D01 author record SHA-256 `a37ee38c396be766b8de364994d6d21913087b1372b6cf41249fedc1fc5e3c3a`. Its two pristine brackets passed. The author stopped at the old dynamic `GetDirectionReference` call, before any measured mass, source save, edit or fresh reopen. Successful non-null extrusion construction does not qualify geometry.

The actual hinge directions were `-Y` and `+X`. Its positive unflipped angles `a=0.2173`, `b=0.4879` produced normals `(cos(a),0,+sin(a))` and `(0,cos(b),+sin(b))`. These match independent Rodrigues rotation about those real directed hinges within `1e-14`. The preserved predictions had the opposite Z signs. The final actual axis also matches the cross product of the two observed angle-plane normals in reverse A/B order.

The observed `GetParents` arrays are `[Right Plane, Front Plane]`, `[Top Plane, Front Plane]` and `[TiltPlaneB, TiltPlaneA]`. They agree with this directed interpretation. They are dependency observations, **not direct measurements of serialized `f80/f88`**: that attempt never saved a source file. The public selection-to-construction ordering is not statically generalized here. The new source pair instead refuses a different actual directed hinge before creating its angle planes.

The [numeric replay receipt](../measurements/2026/FreecadObliqueCylinderSign01.json) preserves the wrong original normals and their exact differences, independently recomputes the actual observed normals/axis and binds the failure record and static pin. Neither predecessor's cases or predictions change.

## Separate disclosed flip pair

The new profile uses the existing author/observer lifecycle, actual principal-plane selections, typed output invocation, circle/centre relation, positive height limit and selected-axis/selected-plane extrusion. Its two disclosed designs are newly authored mathematical inputs. They are discovery probes, not held-outs.

| Case                      | Initial `(a,b,r,H)` in radians/metres | Edited `(a,b,r,H)`              | Native angle policy                                                             |
| ------------------------- | ------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| F01 `ObliquePositiveFlip` | `(.2831,.4367,.00823,.02637)`         | `(.3719,.2513,.01019,.03461)`   | Both positive target tilts require reverse `true` for the frozen `-Y/+X` hinges |
| F02 `ObliqueNegativeFlip` | `(-.3191,-.1973,.00961,.03289)`       | `(-.2279,-.4073,.00787,.02543)` | Both negative target tilts require reverse `false`                              |

For all ten initial/intermediate/final states, geometry is predicted independently as `d=(H tan(a),H tan(b),H)`, volume `πr²H`, centroid `d/2`, translated-disc extrema, and the integrated oblique cylindrical side area plus two circular caps. Signed plane normals and the ordered direction-axis cross product are frozen separately from the positive-Z analytic extrusion displacement.

Each case requires a fresh pristine before control, native author/edit/save, original fresh reopen, edited fresh reopen, and pristine after control before a hash-only source lock. All ten native process identities must differ across the complete pair. Original and edited native files stay immutable; actual angular/radius/limit-distance ownership, four real driving edits, full tree, warnings, body count, mass, selected direction/end references and saved identity remain mandatory. There is no scalar edit crossing zero, no selected-end type `10`, and no hidden-case execution.

`AuthorObliqueCylinder` gains two explicit argument delegates, preserving its old defaults and all three original call inputs. `AuthorObliqueFlip` overrides only those inputs and adds directed-axis and signed-normal checks. The separate `ObliqueFlipSources` protocol is an explicitly named reuse of the original source-runner logic; all shared oracle helpers remain checksum bound.

## Reproduction and current evidence

Run the independent source pin without executing vendor code:

```sh
python -B re/tooling/sw2026/oblique/PinObliqueCylinderSign.py --root /absolute/Kit --originals /private/licensed/bin --output /unused/SignPin.json
```

Replay only the explicitly disclosed failed author record:

```sh
python -B re/tooling/sw2026/oblique/ReplayObliqueCylinderSign.py --disclosed-author /declared/D01/author.json --static-pin /unused/SignPin.json --output /unused/SignReplay.json
```

Both commands require Python 3.11 or newer. The numeric replay checks exact input hashes and refuses changed evidence. Source preparation uses `ObliqueFlipSources.py prepare` with the existing exact control, prior API manifest, unused private output, explicit guest root and verified guest Python. Root alone runs the generated serial recipe. Preserve a terminal failure and always execute its independent trailing control.

Two independent static-pin processes and two independent numeric-replay processes produced byte-identical receipts. The frozen source packet passed two real host verifies and refused four independently tampered packets. Six owned Python sources pass AST/compile and contain no comments or docstrings. Legacy default argument delegation was verified as the exact narrow delta; both predecessor tool and input identities remained intact. These are host/static facts. The new pair has zero native launches, zero writer outputs and zero held-out reads at this freeze.

## Native disclosed comparison

Six distinct SOLIDWORKS 2026 SP05.2 processes ran the frozen signing and source tools, with four healthy pristine controls. The two new authors passed strict directed hinges, plane signs, live circle/axis/limit ownership and typed extrusion output queries. Both produced one solid and reached the initial independent volume comparison.

| Case | Predicted volume, m³ | Observed volume, m³ | Relative deficit |
| --- | ---: | ---: | ---: |
| F01 | 0.000005611250704191777 | 0.000005611074280887201 | 31.4 ppm |
| F02 | 0.000009542463809139074 | 0.000009541649491561081 | 85.3 ppm |

Both runs stopped before driver edits, save and fresh reopen. The original analytic targets and tolerances remain in the receipt. The observer uses the default mass-property calculation. A separate accuracy-controlled comparison on the same authored geometry is needed to distinguish property evaluation precision from a solid geometry difference. [Native receipt](../measurements/2026/FreecadObliqueCylinderFlipNative01.json) · [Vendor accuracy enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swMassPropertyAccuracyLevel_e.html?id=2.10.1.507)
