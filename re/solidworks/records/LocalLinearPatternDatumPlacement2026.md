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

## Staged height discriminator

The [packet freezer](../../tooling/sw2026/linear_pattern/PatternDatumHeightPacket.py) requires the exact passing `LinearPatternEnvelope02` sibling, its verified control and immutable tool inventory. It keeps the historical packet intact. It freezes the original pure height predictions, both source roles and phases, separately bound script hashes, the native executable hash and the exact new locator. The shared author accepts a single-spacing source specification. The shared phase runner accepts the height observer through its existing author, warning, save and fresh reopen boundary.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/PatternDatumHeightPacket.py \
  --prior-trial /absolute/share/LinearPatternEnvelope02 \
  --output /absolute/share/LinearPatternDatumHeight01 \
  --guest-root '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\LinearPatternDatumHeight01' \
  --guest-python 'C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe'
```

`Recipe.json` contains the single root-owned `guest_argv`. It verifies the freeze and registered libraries before launch. It identifies the getter DISPIDs on the installed major-34 `IRefPlane` and `IMathPoint` interfaces, requires no arguments and a declared VARIANT result, and uses those two exact property bindings. The stages are the pristine control, Short author and reopen, Tall author and reopen, and the trailing control. The two native parts come from distinct authoring sessions. The same selected `EnvelopeHinge`, `EnvelopeDirection` and `SeedBoss` roles are bound in both. The observer records raw finite on-plane diagonal endpoints before selection, directly after pattern creation, after the authored rebuild and after a fresh reopen. Native source scope requires one joined solid with the fixed XY profiles, stock and seed dimensions, the actual 20 mm pitch and count two, plus independent volume, area, COM and six exact extents in each applicable phase. [Native source runner](../../tooling/sw2026/linear_pattern/RunPatternDatumHeight.py) · [Native display observer](../../tooling/sw2026/linear_pattern/AuthorPatternDatumHeight.py) · [SOLIDWORKS 2026 bounding-box example](https://help.solidworks.com/2026/english/api/sldworksapi/Get_Coordinates_of_the_Plane%27s_Bounding_Box_Example_CSharp.htm)

After an exact clean result, the host audit verifies both control and four candidate digests, actual isolated process lifetimes, preserved XY profiles, named source references and immutable saves. It replays both linked streams, captures the exact `fc8` bytes and compares the measured centres at the four checkpoints, the stored datum display geometry and the independently predicted stock projections. A stage must show at least a 1 mm measured transverse contrast to distinguish the height arms. Match tolerance stays 5 nm. Coincident matching stages remain unresolved as a lifecycle question. A typed archive refusal is retained without suppressing the native observations. The hypothesis for a 5% border is assessed separately from measured geometry and remains unqualified. [Host audit](../../tooling/sw2026/linear_pattern/AuditPatternDatumHeight.py)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPatternDatumHeight.py \
  --trial /absolute/share/LinearPatternDatumHeight01 --packet-sha256 TRIAL_SHA256 \
  --result-sha256 NATIVE_RESULT_SHA256 --output "$(mktemp -d)/DatumHeightEvidence.json"
```

## Measured height discriminator

Packet `a193b7e1eeaa9641f92e89a8e3c6697fe6843568ffc30a410979089ef4d07ceb` completed four candidate phases and both pristine controls across six distinct exact-build processes. Both saves and fresh reopens were clean. All 122 numerical checks passed, and the exact XY profiles, actual datum/hinge/seed ownership, pitch, count and tree matched. The verified Automation property gets had DISPIDs 4 for `IRefPlane.BoundingBox` and 3 for `IMathPoint.ArrayData`, each no-argument with VARIANT result. The native receipt SHA-256 is `5e28d6a87d55e1de2ee31ebe57d3321fe6bf1759ccd6d6a5bb99dbb264777fb8`. [Exact host audit receipt](../measurements/2026/LocalLinearPatternDatumHeightNative01.json)

| Arm | `fc8` model-space point (m) | Error from live diagonal midpoint (m) | Error from frozen hinge-square prediction (m) | Error from stock projection (mm) |
| --- | --- | ---: | ---: | ---: |
| Short, 8.625 mm seed boss | `(0.003354337793253686,0.003354337793253686,0.004312500000000001)` | `6.133173666733497e-19` | `1.5023145987371592e-18` | 69.5024620246 |
| Tall, 20.375 mm seed boss | `(0.00792401536667175,0.00792401536667175,0.010187500000000002)` | `0` | `3.0046291974743185e-18` | 63.0399620246 |

Each saved point matches its typed local rectangle midpoint bit-for-bit. Each live display diagonal matches the corresponding two typed saved corners exactly. The display centre's model-space transverse coordinate shifts 6.4625 mm between arms at every stage, with the projected stock XY fixed. The predicted hinge-square and independent shape checks pass. The stock projection is refuted for this independent pair. Each arm repeats the same display rectangle at preselection, creation, rebuilt and fresh-reopen stages, leaving the native point update trigger unresolved.

The two native saves each re-emit both linked streams exactly, with identical concrete read and write map states. The next slots are 112 and 472 and the span `30355–30379` carries the 24 point bytes in each ResolvedFeatures stream. The host receipt also retains the typed owner identities and raw points. The measured relation applies to this disclosed through-origin constrained angle family. Source sizing and wrapper construction still require their causal loader path and any complete writer needs independent native qualification.
