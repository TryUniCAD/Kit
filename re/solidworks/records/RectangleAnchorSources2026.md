# Origin-anchored rectangles in SOLIDWORKS 2026

The two disclosed sources cover a lower-left corner at the model origin and a rectangle centered on that origin. Both native sketches report constraint state 3 after adding two driving lengths. Each produces one ordinary forward blind boss. The native creation calls are `CreateCornerRectangle` and `CreateCenterRectangle`. The center operation creates the edges and their construction diagonals. [Native API](https://help.solidworks.com/2018/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchManager~CreateCenterRectangle.html)

The source job was frozen at `63187e7839de95dfea7169d4415149e16289b1ec`. Four source author and fresh reopen processes ran between two pristine controls on SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The six saves include each original, its independent width edit and its independent height edit. All six preserved the named driving parameters, full relation bindings and ordered feature tree when reopened. The corner stayed at zero. The centered profiles retained their origin centroid within floating-point tolerance. The body count, volume, area and center passed 292 numeric comparisons. [Native and typed source receipt](../measurements/2026/RectangleAnchorSource01.json)

## Archive ownership

The readback uses the frozen Config codec snapshot `a29529d10ad19fc127083c8a54ec4f456f345570a3a7db44486aeb3884eb9012` and the auditor `205acf570a59276bc57a9278af09fd64fd29ffbc929641f677f822f95bbed8a3`. CMgr, CMgrHdr2, Config-0, ModelHeader, ResolvedFeatures, Definition and Header2 round-trip for each sibling, giving 42 exact comparisons. ResolvedFeatures inherits Config's actual map. [Source auditor](../../tooling/sw2026/serial/AuditRectangleAnchorSources.py)

| Owner | Observed field relationship across the six siblings |
| --- | --- |
| Origin profile | The selected origin point belongs to the separate `moOriginProfileFeature_c`. Its sketch contains one point. The persistent feature ID and creation stamp are carried by the component sketch handle, with a distinct local point slot. |
| External point inside the authored sketch | A kind-1 point carries `sgExtEnt_c`, then `moSketchExtRef_w`, then `moCompSketchEntHandle_c`. The handle points to the actual origin profile and its first point. The wrapper also carries `moPointBackedUpData_c`. The embedded `moUnitComponent_c` is a separate mapped instance from Config's self component in these sources. |
| Corner coincidence | An `sgLogG2Dim` with `f80=9` owns two `sgPointHandle` records. One selects the external origin entry and one selects the boundary corner. Both points have local sketch coordinates zero. |
| Center coincidence | Two other `sgLogG2Dim` records of type 9 each tie the local center to one diagonal through a `sgPointHandle` and an `sgLineHandle`. The third joins the referenced origin to that local center. |
| Width and height | Two `sgPntPntDist` entries and four unary horizontal or vertical relations persist alongside the origin constraints. The four ordinary boundary edges define the boss. |
| Reference state | The six source sketches have `f188=0` with the external point present and zero entries in every separate coincidence map. Native constraint ownership resides in the binary logical dimension array. |

The independent source lock binds six qualified phases including both pristine controls, the hidden recipes and both original and edited artifact manifests. The corner constructor now has a guarded generated archive. The centered profile's construction diagonals and coincidence ownership still need construction. [Corner construction](RectangleCornerAnchorConstruction2026.md) · [Dimension construction](RectangleDimensions2026.md) · [Pre-writer lock](../v2026/heldout/RectangleAnchorSourceLock01.json)
