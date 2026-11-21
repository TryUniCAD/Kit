# Local linear-pattern direction datum display placement

The two whole-solid envelope hypotheses failed on the disclosed SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. Both native controls and all four candidate phases passed in six distinct processes. The 20 mm original and 36 mm edited save each reopened with zero errors and warnings. The 122 recorded numerical checks passed, including the datum frame, joined solid, spacing and declared dimension values. Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. [Frozen experiment](LocalLinearPatternEnvelopeContrast2026.md) · [Unchanged negative result](../measurements/2026/LocalLinearPatternEnvelopeNative02.json)

## Measured result and exact replay

Packet `60620b7cf6072b729e55f615d4d6e2b14f7e7dfb7a43407303e24e788dc1f328` binds native receipt `c46b85d6ee72bafcbb438c4f70813966fdcf37331585bdb6970b531fbb21b5be` and observer revision `72b942ede352261cdc955af43872904e9aea3df8`. The original host audit `2c63cd870f5252e4a80f12ce863d9ca6d0ea20385cf2b46667a6ec76478b6338` returned `outside_fixed_hypotheses`. The initial projected-stock point missed by 67.5087120246 mm. The edited point missed the projected final envelope by 68.7305374315 mm.

The two linked archive replays return byte-identical Config-0 and ResolvedFeatures streams and equal concrete read/write maps, using the re-emitted Config-0 map for the ResolvedFeatures write. Both runs resolve the selected `moLineRef_w` at map object 457, the separately allocated unit component at 459, datum ID 45 at the same creation epoch and seed feature ID 40. The Config-0 next slot is 112. The ResolvedFeatures next slot is 472. The original test's 24-byte `fc8` range moves from `30355–30379` to `30597–30621` as the edited feature stream grows by 242 bytes. Its 24 bytes stay `33bde5ed8d83733f33bde5ed8d83733f4a0c022b8716793f`, or `(0.004764131938244365, 0.004764131938244365, 0.006125)` m, in both saves. [Reciprocal linked and display comparison](../measurements/2026/LocalLinearPatternDatumPlacement01.json)

## Bound candidate owner

The actual selected plane is `moRefPlane_c` ID 45 with constrained angle data `moConstraintCoincLineAtAnglePlaneRefplaneData_c`. Its geometric root is zero. Its common `moRefPlnData_c` display borders are `(0.0012862500000000003, -0.013536250000000001, 0.014148750000000002, -0.0006737500000000001)` m. The two column vectors of its `f20` transform in model space are `u=(0,0,-1)` and `v=(1,1,0)/√2`, exactly equal to the live transform. The display origin of the principal default planes is their separate `display_root`.

For these exact linked datum types, evaluate the display rectangle's midpoint at `origin + ((b0+b1)/2)*u + ((b2+b3)/2)*v`. Its binary64 coordinates agree bit-for-bit with both oblique `fc8` rows. The independent name-location owner `moRefPlane_c.f6c0` equals `origin + b1*u + b2*v` exactly. The same relation produces all six previously disclosed principal points within one component ULP. All three D01X rows are bit-exact. All three D02Y X coordinates are one ULP below the recomposed value, a difference of `1.3877787807814457e-17` m. Both native pattern edits of each principal case leave its selected display centre fixed. All six principal source Config-0 and ResolvedFeatures pairs also re-emit exactly with equal linked map states. [Prior typed principal result](LocalLinearPatternTypedArchive2026.md)

The currently bound `moRefPlnData_c::getFourCorners` at `0x4c2e57c0` consumes the actual plane origin, border array and basis. The separate native name-location routine `0x4c2f72c0` selects a corner and publishes `f6c0`. The current evidence locates the reference plane display rectangle and gives an exact geometric relation in this cohort. The selected-plane branch that populates `moLineRef_w.fc8`, its floating-point operation order and its update triggers still need independent evidence. [Exact-build corner and name-location evidence](DrawingScaledSupports2026.md#concrete-native-owner-paths)

The observed hinge endpoints are `(0,0,0.0128625)` and `(0,0,-0.0006125000000000002)` m, independently equal in the linked `moPlaneInterAxisData_c` and native observer. A candidate sizing rule places a square of side equal to the finite hinge span `13.475` mm between its true endpoints and toward positive local `v`. Adding a 0.67375 mm margin to all edges matches the four saved borders. The vendor documents automatic sizing from defining geometry or model bounds and a 5% enlargement. The particular hinge square, per-edge padding and update stage remain hypotheses for this constraint. [SOLIDWORKS 2026 automatic sizing](https://help.solidworks.com/2026/english/solidworks/sldworks/t_Automatic_Sizing_of_Planes_and_Axes.htm)

## Next disclosed discriminant

Freeze two independently authored seed depths of 8.625 and 20.375 mm. Keep the original XY rectangles, 5.75 mm plate and 20 mm pitch. In both arms the copied seed stays within the plate, and the union preserves one body. The predicted projected stock centres share their XY components `(52.5,52.5)` mm. The hinge-square prediction gives display-centre triples `(3.3543377933,3.3543377933,4.3125)` mm and `(7.9240153667,7.9240153667,10.1875)` mm, a 6.4625 mm transverse separation. Their respective distances from the stock projections are about 69.50246 and 63.03996 mm. The independent volume, exterior area, COM and exact extents are computed for both pre- and post-pattern solids before opening the oracle. [Pure height comparison](../../tooling/sw2026/linear_pattern/PatternDatumHeightContrast.py)

Use the same pin-checked oracle with both pristine controls. In each independent author phase, after authoring the plane but before selecting or creating the pattern, read its actual display diagonal via the declared `IRefPlane.BoundingBox` property and both `IMathPoint.ArrayData` values. Preflight the registered major-34 member. Require two distinct finite on-plane coordinates, an independently checked frame and the actual hinge and plane references. Record the same diagonal after creation and after a fresh reopen, plus the exact saved `fc8` and replay. Compare the line point against the measured diagonal midpoint at all stages with a 5 nm tolerance. A meaningful change in the native midpoint between the two arms tests the display hypothesis directly. A lack of measured midpoint movement makes the contrast inconclusive. If the measured pre- and post-selection display centres differ, resolve the lifecycle stage separately. [SOLIDWORKS 2026 reference-plane bounding-box example](https://help.solidworks.com/2026/english/api/sldworksapi/Get_Coordinates_of_the_Plane%27s_Bounding_Box_Example_VB.htm)

No new native execution, held-out read or writer took place. The observation is limited to the eight disclosed saves. The new height comparison is prospective.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPatternDatumPlacement.py \
  --trial /absolute/share/LinearPatternEnvelope02 \
  --principal /absolute/share/LinearPatternSourcePacket03 \
  --negative re/solidworks/measurements/2026/LocalLinearPatternEnvelopeNative02.json \
  --output "$(mktemp -d)/DatumPlacement.json"

python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternDatumHeightContrast.py
```

The prospective height JSON SHA-256 is `8325f3457f0e7d2a565a63d3bd4a718a70cf736d8a14d7045ca218dfe7d9354b`.
