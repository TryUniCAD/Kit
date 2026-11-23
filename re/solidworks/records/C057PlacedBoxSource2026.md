# Disclosed native source acquisition for the C057 oblique box

Task B04-SW2026-FCSTD, [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The source packet is pinned to aggregate `f835b1395a6e0159e2e08ae45d26a3239e0151ed` and SOLIDWORKS 2026 SP05.2 build 34.5.2.0604. It prepares disclosed native discovery before a placement writer exists. Native qualification is pending. [Prior stock proof](SdkFreecadPlacedStock2026.md) · [Existing offset source author](../../tooling/sw2026/AuthorReferencePlaneSources.py)

The host freezes actual `Box001` from C057-P01. It authenticates the case's FCStd and bound OCCT Shape, the property object ID 4972, the three source dimension aliases and values, the stored placement and its independently agreeing quaternion and axis-angle. The original is 200 × 500 × 100 mm at (2000, 6000, 0) mm. Its directed hinge is (-2, 1, 0)/√5 and the angle is 0.6405223126794245 radians. The plane normal is (1, 2, 3)/√14. The same source proof matched all eight world vertices, twelve edges and six outward faces using rigidly transformed local corners. The selected stock is one primitive of the actual FreeCAD document. The second packet case uses independent authored dimensions, a different translated hinge, the opposite sign and independent edits. Both cases are disclosed controls.

## Exact acquisition

1. The recorded installation reads the major-34 interface and constant metadata before CAD. It binds the ordered `InsertRefPlane` arguments, native methods and actual relation enums. Verify the executable digest and complete file version on every app process.
2. Freeze the independently predicted world shape and values before authoring. Pin the unchanged L1 boss and principal Top revolve controls at `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6` and `4bf2c202be9ae4fc7786e50a92c4f83dc17ea4bc80492b7173075d74f678d3f0`. Run both on each side of the batch.
3. Create the real finite construction line on the Front plane through the desired world anchor. Fix its two actual points. Use the actual directed segment and normal to compute the signed angle. Select the plane and line at marks 0 and 1. Read the active selection slots before the angle operation and verify both ownership slots through the resulting `IRefPlaneFeatureData`. [2026 plane constraints](https://help.solidworks.com/2026/english/SolidWorks/sldworks/hidd_dve_create_plane.htm)
4. Record the whole created datum and attached sketch frames before authoring the rectangle. Check signed normals and plane incidence independently. The rotated stock's source X is 26.565° from the opposite hinge. Use the real sketch inverse and preserve that in-plane roll when projecting the four stock edges. The sketch carries a separate fixed construction guide, a fixed first corner, aligned parallel and perpendicular relations, and two selected true-length dimensions. Check the returned native display class, actual driving parameter and owner. Restore the native dimension prompt preference immediately after the two dimension calls. [2026 relation API](https://help.solidworks.com/2026/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.isketchrelationmanager~addrelation.html)
5. Create one ordinary blind boss and measure the complete recursive feature tree, resolved dependency names, editable dimensional owners, eight world vertices, six faces, twelve edges, volume, area and centroid. Match the future support gauge to the actual native frame only after measuring it. Each Length, Width, Height and Angle derivative changes one driver from the exact original state. Restore and remeasure the original values and corners between edits. Save separate SLDPRT, STEP and Parasolid text siblings, hash every file, then fresh-read every native derivative and the original read-only. Require unchanged artifact digests and matching actual datum, sketch and driver ownership.
6. A failure preserves the actual call trace and any available datum checkpoint. Run both trailing controls independently. A summary requires all eight serial native lifetimes, healthy matching before/after controls, complete source reopens, and identical author snapshot digests. Source-only work contributes zero Kit outputs and zero conversion acceptance. Private pre-writer cases require a separate lock protocol after this disclosed qualification.

## Reproduce

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/primitive_stock/C057SourcePacket.py \
  prepare /absolute/new/packet --inventory /absolute/path/VerifiedInputs01.json \
  --guest-root 'C:\KitC057PlacementSource01'
```

Use the frozen copy of `C057SourcePacket.py` in the reserved guest with Python 3.12 and `-E -B`. Supply `run PACKET_JSON PACKET_SHA PHASE` with these phases in order.

1. `Metadata`
2. `BeforeL1` and `BeforeRevolve`
3. `AuthorC057Box001` and `ReopenC057Box001`
4. `AuthorSignedRollContrast` and `ReopenSignedRollContrast`
5. `AfterL1` and `AfterRevolve`

Native traces remain in the numbered guest-local directory under `PACKET_SHA\Slot00\T01`. The `summary PACKET_JSON PACKET_SHA NEW_RECEIPT` command emits counts, digests and verdicts only. The frozen source packet digest is `83b39c56846150a8c79eb13fd63a62f542293d044dcb9df9495f788a54266154`. The independently predicted states digest is `46a8c2d0a139f75f00581defe73fa9d2889984cc63230efa6a5510ff8ea19f5b`. Two fresh host verifiers agreed, eight analytic edit contrasts passed and six altered or out-of-scope requests refused. The guest still needs to establish the actual selected sketch-line datum, roll, dimensions and lifecycle on this exact freeze. [Host preparation receipt](../measurements/2026/C057PlacementSourcePreparation01.json)

The frozen `Metadata` phase passed at 2026-11-23T12:28:10.673Z in the Windows 11 guest. The installed major-34 type libraries supplied the required method signatures and enumeration values. A separate guest file hash matched the phase receipt's binding digest `2f6b7bbdc671f9a7c1d84c14d6a870a55ffe922065fc2b8943b5535856506f73`. This phase used zero SOLIDWORKS processes. The guarded native source phases require passing application controls.
