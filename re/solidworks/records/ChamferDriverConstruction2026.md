# Model-derived live distance and angle for a single-edge chamfer

Task `B04-SW2026-EDGE-CHAMFER`, PR #121, owner `/root/assembly_frontier`. This is an internal construction step for the ordinary schema-one, type-10, single-edge angle-distance chamfer on an axis-aligned rectangular stock. It uses the [typed physical and driver read](ChamferTypedArchive2026.md), [independent bevel model](../measurements/2026/EdgeChamferModelBoundary01.json), shared annotation catalog and current 19000 resolved dimension serializers. The exit check for this step is complete standalone construction and typed re-emission of both live driver chains with actual registered model view owners. The selected-edge and result keepers, complete resolved feature, native lifecycle and independent writer qualification remain open.

## Owners and value derivation

[`MakeChamferDrivers.py`](../../tooling/sw2026/edge_chamfer_source/MakeChamferDrivers.py) accepts a fresh `Chamfer_c` owned by the generated part, explicit stock bounds and selected edge/incident side, positive SI distance and acute angle, and explicit display intent. Its input supplies the annotation view **name**, linear text station and signed clearance, angular label location in plane coordinates, angular witness length, the ordinary design-intent flag and independently supplied leader integers. The scope requires the measured signed local X-and-Y orientation and linear text beyond the second witness. The angle label must classify as exterior to the first witness. An unsupported label state, ambiguous view, alternate mode or invalid driver ownership refuses before consuming either ID.

| Field group | Ownership and rule |
| --- | --- |
| `f810` / `f818` | Distance / angular display roots on the actual feature. Each owns one local `moFeatureDimHandle_c` with a reciprocal retaining collection. The typed value owners are `ParallelPlaneDistanceDim_c` and `AngleDim_c` and their unregistered parameters carry the native ordinal names D1 and D2. The shared allocator supplies the two `f50` values in that order before the feature's separate ID. |
| `f28.f58`, `f5b0`, text subtype | The two live values are positive metres and radians from the neutral geometry. Each display packs its own value into one binary64 element using the shared allocation rule. Mode 10 uses factory text kinds 18 and 13. |
| `f2b0`, `n2b0`, `f58`, style | The display joins exactly one actual `moAnnotationView_c` in the part catalog by its generated ID. The separate inherited `f58` remains its constructor value zero. Both displays project the part's ordinary zero-tolerance free text style. The common raw transform uses the [initialized identity and ignored padding](SdkDrivingDistanceConstruction2026.md#knowledge-and-field-classes). |
| Value frame and D1 world points | For selected edge midpoint `M`, outward D1-side normal `U` and the other outward normal `V`, the origin is `P = M - D1*U`. Apply the actual catalog rotation to this new origin through the shared inverse transform. D1 owns `f80=P`, `fa0=M`, zero `fc0` and its own `fe0=U`, `fe8=V`. |
| D1 display geometry | In the view frame the first witness is zero and the second is `Q = local(M - P)`. Its two second witness rows are both `Q`, its direction `fa38` is the signed X axis and its separation `fad0` is D1. The independently authored linear text location supplies station, clearance and direction. |
| D2 value and display geometry | The first world witness is `P + R*(-cos(D2)*U + sin(D2)*V)`. The second is `P - R*U`. `fc0` is `P`. In the view frame the two normalized inward rays meet at zero. Their two farther points are the local witnesses and both anchors are zero. The projected far distances are `-R`, near distances zero, and the witness chord `fad0 = 2*R*sin(D2/2)`. |
| D2 label and arc tail | The authored local text point yields unit direction and radius. For inward rays `u,v` and label direction `d`, the [shared native first-exterior rule](LocalLinearPatternAngularArc2026.md#construction-and-update) supplies station `-0.5` when `dot(cross(u,d),cross(u,v)) < -1e-8` with reliably positive signed witness order. The generic feature arc retains its constructor `f100c=0`, `f1010=1`, `f1008=1` and `f1018=0x18` on this branch. |

The shared admission in [`RequireChmfView.py`](../../../src/convert/adapters/solidworks/Archive/Construction/Dimensions/RequireChmfView.py) checks the exact class, ordinary mode and release, local retaining handle with null external owner roles, typed D1/D2 parameter and owner identities. Existing resolved root admission and normal registry modes stay unchanged.

## Evidence

Separate guarded source processes read the exact four originals and edited derivatives from the [disclosed lock](../measurements/2026/EdgeChamferDisclosedSource01.json). All four join their true annotation plane and match the independent edge, transform and witness geometry within `1e-12` m. The two native files assign ID 201 to different views. Axial A uses `*Back`. Transverse B uses `*Left`. D1 clearance in A stays 0.004125 m when its driver changes from 0.004125 to 0.005625 m. Both independent edit paths change D1 `f8a4` by `0x02000000`, even when only D2 changes. The generation branch uses fresh style state. The native edit flag and automatic presentation defaults require further evidence.

| Disclosed state | D2 rad | D2 chord m | First-exterior score | Actual `f8a8` |
| --- | ---: | ---: | ---: | ---: |
| Axial A original | 0.5017821599483697 | 0.004965344787474323 | 0.0808722863177775 | 1.5 |
| Axial A edited | 0.5017821599483697 | 0.004965344787474323 | 0.08087228631777743 | 1.5 |
| Transverse B original | 0.619591884457987 | 0.006097285980560215 | 0.08705744372276414 | 1.5 |
| Transverse B edited | 1.069014166846527 | 0.010188338736816835 | -0.2582005033228347 | -0.5 |

The native 10 mm witness length is a scoped observation. The independently authored model requests use 14 and 16 mm with independent offsets, driver values, view order and allocation origin. Each makes a complete 3,657-byte typed two-root driver graph using its own generated Config-0 inheritance. They have distinct exact digests and join annotation IDs 200 and 202. Four isolated model workers produce deterministic bytes and read them through the shared strict chamfer dimension reader. Their new graphs retain the original eight distinct vertices and stable ordered identities. The malformed probes include invalid modes, crossed and external handles, the wrong annotation orientation, incompatible text state, invalid acute values, bad leaders, duplicate attachment and insufficient allocator space. Every refusal preserves exactly the feature and allocator state. [Sanitized process receipt](../measurements/2026/EdgeChamferDriverConstruction01.json)

```sh
python3.14 -I -B re/tooling/sw2026/edge_chamfer_source/ProveChamferDrivers.py \
  --compare /absolute/path/to/disclosed/EdgeChamferSource04 \
  /absolute/unused/EdgeChamferDriverConstruction01.json
```

The source worker reuses the pinned typed archive reader and exact disclosed intake. Model workers use only stdin intent and shared constructions after activating the file and process audit. The standard committed-fixture research CLI lacks this opt-in mode and a guarded in-memory graph-generation phase. The proof uses the existing worker and archive automation at those actual boundaries. It opened no native application or protected input and generated no CAD file.

## Next discriminator

The `+1.5` text state occurs in three native snapshots. Its full condition and automatic initial layout remain unclassified. The smallest independent contrast is one disclosed ordinary edge chamfer held at the same live D1/D2, selected edge, view and style. Save three derivatives with explicit D2 label positions in the first exterior, interior and opposite exterior regions, then read the actual local label direction and station from each. Verify the installed annotation accessor and setter first, restore the same two typed dimension chains, check the model's six-significant-figure physical invariants and preserve a no-change rebuild/save as the D1 flag control. Bracket the measured native phases with healthy controls and reopen each derivative with no errors or warnings. [SOLIDWORKS 2026 annotation accessor documentation](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IAnnotation.html)

The whole feature still needs independently constructed selected-edge wrappers and keeper associations, especially the positive edge `f70` identity and `f8c8` word domain identified by the [physical proof](ChamferTypedArchive2026.md#physical-rollback-and-bevel-ownership). Existing source replay cannot supply those associations to the writer.
