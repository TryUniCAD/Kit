# Draft section: independently authored part features

This draft is for `Documentation/Reference/Research/FusionDataModel.md`.
It is kept here because that document is maintained in a separate change.

## Independently authored part features

`DocumentSpec.Features` adds an ordered tuple of part features to an unconstrained cuboid or to a part profile. With `ProfileKind="part"`, the first feature must be a `new` `ExtrudeSpec`, and no other feature may create a body. `CheckFeatures` accepts at most 16 features, requires a shell to be last and reserves generated `d<digits>` parameter names. `SolvePart` applies each feature to an exact prism model in millimetre inputs and centimetre geometry. The model is a stack of slabs with vertical walls and flat caps, so every authored surface is a plane or a vertical cylinder. Rejected profiles, missed bodies, collapsed sides and over-thick shells raise `ValueError` before any record is written.

| Family              | Design feature          | Operations          | Journal state | Driving parameters                                    |
| ------------------- | ----------------------- | ------------------- | ------------- | ----------------------------------------------------- |
| Sketch extrusion    | `DcExtrudeFeature`      | 3 with its sketch   | One           | `AlongDistance`, `AgainstDistance`, `TaperAngle`      |
| Hole                | `DcHoleFeature`         | 1                   | One           | `HoleDiameter`, `HoleDepth`, `TipAngle`, `CBDiameter`, `CBDepth` |
| Rectangular pattern | `DcRectangularPattern`  | `CountU` × `CountV` | One           | `countU`, `CountV`, `uSpaceDistance`, `vSpaceDistance` |
| Circular pattern    | `DcCircularPattern`     | `Count`             | One           | `countU`, `TotalAngle`                                |
| Offset plane        | `DcWorkPlane`           | 1                   | None          | `AlongDistance`, `ExtraOffset`                        |
| Construction axis   | `DcWorkAxis`            | 1                   | None          | None                                                  |
| Construction point  | `DcWorkPoint`           | 1                   | None          | None                                                  |
| Mirror              | `DcMirrorPattern`       | 2                   | One           | `countU`, `mirrorStitchTolerance`                     |
| Fillet              | `DcFilletEdgeFeature`   | 1                   | One           | `TangencyWeight`, `Radius`                            |
| Chamfer             | `DcChamferFeature`      | 1                   | One           | `Distance`, `Distance 1`, `Distance 2`, `Rotate Angle` |
| Shell               | `DcShellFeature`        | 2                   | One           | `innerThickness`                                      |

A sketch extrusion writes a `DcSketch` on the origin XY plane with its lines, arcs and circles, the region recipe and the profile. A `new` extrusion owns the body. A `join`, `cut` or `intersect` extrusion adds a body target with tracking type 8. One-sided, flipped, symmetric and two-sided extents use the native extent records.

A hole writes a `DRPoint` on the current top face and a `DRVector` with `refType` 19 along +Z. Both carry `param`, the offset of the hole centre from the plane root of the top face. An extruded cap face has its root at the centre of the bounding box of its sketch profile, with u along +X and v along +Y. A hole at the root uses `refType` 6 and a plain face recipe. Any other hole uses `refType` 17 and the bound face recipe of the top face. A top face with one circular boundary uses a single-edge recipe that names the rim edge tag. A through hole adds a body extent reference with tracking type 5. A blind hole has a 180° tip, so its floor is a plane. A counterbore adds `CBDiameter` and `CBDepth`.

A rectangular or circular pattern copies an earlier cut extrusion or hole. A mirror copies one about an earlier offset plane parallel to YZ. The copy writes `DcPatternSource`, a `ModelDataRef` and an `EntityDataRef` to the source feature. It adds one `DcPatternBodyOccurrence` per copy and an `occOperationIdsMap` entry per copy after the source. Rectangular occurrence tags follow `(u + v)(u + v + 1) / 2 + u + 1` with U varying fastest. Circular and mirror occurrence tags count from 1. Source walls and floors carry a `TrackAttrib` that names the source reference. Copy faces, floors included, carry the source tag plus the pattern and copy operation identifiers. A circular pattern or mirror names one face in `DcPatternSource.adjacentFaceCaches`. For an extrusion source, Kit names the base face, where the source sketch lies. With the top face, a later hole warned after the first `computeAll` in 36 of 82 probe runs. A rectangular pattern uses the X and Y origin axes. A circular pattern turns about the Z axis. The mirror's `countU` and `mirrorStitchTolerance` stay out of `allParameters`.

A fillet or chamfer writes one `BrepRef` under its `ModelDataRef` target for each selected vertical edge. Each edge also adds one progenitor seed, and the progenitor table `tagId` is the edge count plus one. The new faces carry primary identifiers 1, 2 and so on in selection order, all with the feature's single operation. A chamfer writes one `primaryIDRowIndexMap` row per edge. `DcChamferData.chamferType` is 1 for an equal distance, 2 for two distances and 3 for a distance and an angle. Type 2 links `chamferDistanceTwoParam` to `Distance 2`, and type 3 links `chamferAngleParam` to `Rotate Angle`. In both native controls the first distance runs along the side that ends at the corner in the counter-clockwise profile.

An offset plane writes a `WorkPlane` before its `DcWorkPlane`, a base `EntityDataRef` to the origin plane and a `DRMatrix` with the plane frame. The plane has start and end state −1, an empty feature user name and the plane name on `WorkGeometry.userName`. It consumes one operation identifier but no journal state.

A construction axis on a vertical body edge writes a `WorkAxis` before its `DcWorkAxis`, whose `creationType` is 4. The axis `DRVector` has `refType` 8, `axisTrackType` 8 and the edge as `line3d`. Its edge `BrepRef` has tracking type 33 and an `ETCachedLineSeg3d` cache. The edge recipe names the incoming wall, the outgoing wall, the floor and the roof, with `ReferenceFaceIndex` 0. The `WorkAxis` line starts at the bottom vertex and spans the edge, with parameters −0.1 to 1.1.

A construction point on the bottom vertex of that edge writes a `WorkPoint` and a `DcWorkPoint` whose `creationType` is 0. Its `DRPoint` has `refType` 10. The vertex `BrepRef` has tracking type 513 and an `ETCachedPoint3d` cache. The vertex recipe lists the floor, the outgoing wall and the incoming wall. Both features behave like the offset plane. They have start and end state −1, an empty feature user name, one operation identifier and no journal state. Each raises `highWaterMarkAxes` or `highWaterMarkPoints` on `WorkGeometries`.

A part can hold up to 16 bodies, numbered in creation order. A later `new` extrusion or revolve allocates another `Body` and `DcBody`, whose `creationIndex` is the body number. A `DcCombineFeature` names each tool body through a `ModelDataRef` with tracking type 5 and a `DRBody` with tracking type 9, whose topology cache points at the tool body tag. The target uses tracking types 4 and 8. `booleanOperation` is 0 for join, 1 for cut and 2 for intersect. The feature has one operation identifier, an empty progenitor table with `tagId` 1 and an `OccurrenceDataRef` keyed in `occDR2FeatIdMap`. A consumed tool stays in the journal, its `Body` is hidden, its `DcBody` is eliminated and the combine lists it in `removedBodies`. A `DcSplitBodyFeature` with its `DcSplitFeature` group names the plane through a `ModelDataRef` with tracking type 33 and an `EntityDataRef` with an `ETCachedPlane`. The lower piece keeps the body, and the upper piece gets a new body in `dcBodies`. A body pattern is a `DcRectangularPattern` or `DcCircularPattern` with `computeType` 2. Its `DcPatternSource` caches the source `DRBody`, and each copy is a new body with a `BodyProgenitor` whose identifier is the new body's `persistentId`. `BRepHistorySerializer.mapBodyId` maps every body tag, and `Bodies.children` lists only the visible bodies.

A loft takes four operations and four timeline items: the base sketch, a `DcWorkPlane` offset from the XY plane, a top sketch on that plane and a `DcLoftFeature` with `booleanOperation` 4. The top sketch's `EntityDataRef` recipe names the `WorkPlane` entity, and its `CoordinateSystem`, `DRMatrix` and `ETCachedPlane` carry the plane offset. The feature holds two `DcLoftSectionData` records, each with a `ModelDataRef` and `SketchRegionRef` scoped to its sketch, and a `DcLoftToolBody`. Its progenitor table lists one `LoftProgenitor` per pair of matching curves from tag 3, each with the lower and upper `SketchCurveProgenitor` and empty neighbour lists, and then the `BodyProgenitor`. The body progenitor lists face labels 1 to n + 2, so both caps appear with the sides. The journal tags both caps and every side with the loft operation and has no sketch curve links. Kit pairs the curves by their order, and each pair must be parallel lines or coaxial circles, so every side is a plane or a cone.

A sweep takes three operations and three timeline items: a rectangle sketch on the XZ plane, a path sketch on the XY plane and a `DcSweepFeature` with `booleanOperation` 4. The feature names the profile through `profileDataRefs` and the path through `rSweepPathsRef`. The path is a `ModelDataRef` with tracking type 5 whose `dataRefs` hold one `EntityDataRef` for each path curve. Each of these holds a `SketchCurveEntityRecipe`, an `ETCachedLineSeg3d` or `ETCachedCircleArc` cache, and progenitors for the curve and its two end points. The feature also holds a `DcSweepToolBody` and six parameters, of which only `AlongDistance`, `TwistAngle` and `TaperAngle` appear in the Fusion API. Its progenitor table lists one `EntityProgenitor` for each path curve from tag 3, then one `SweepFaceProgenitor` for each face tag, then the `BodyProgenitor`. The floor and the roof are single faces that carry one tag for each path segment. The [sweep faces gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Features/FeatureSweepFaces.md) records the tag order. Kit sweeps only a rectangle, along a path of smooth lines and arcs that leaves the origin along +Y, so every wall is a plane or a vertical cylinder.

Feature `n` takes the next state ID after the last solid feature. `LinkTimeline` updates the creation order, the entity and feature identifier maps, the per-class `featureIndexMap` and the component `operationSeedId`. Parameters use `d<n>` user names after the existing parameter watermark, and their expressions omit a trailing `.0`.

`EmitPartHist` writes one journal state for each solid-changing feature. Each state contains the complete solved body. A face that keeps its draft key across two states is a modification and keeps its tag. A face whose key changes is a deletion plus an insertion, and the inserted face receives a fresh tag. The body claims tag 0 before any face. That tag must equal the `mapBodyId` key of `BRepHistorySerializer`, or Fusion shows a body without geometry.

Every bulletin names the object entity on its new side. A modified object keeps one entity, and each modification stores a backup of the earlier data on its old side only. Kit first wrote each earlier version as the created entity and as the next backup. Fusion opened and rolled back those journals, then terminated in `HISTORY_STREAM::delete_delta_states` while it disposed the closed documents. The 43 native controls that the Kit journal reader accepts all follow the identity rule.

Every reference scope (`BrepRef.rScope` and `ETCachedTopology.scope`) carries the component `persistentId`. A body identifier in this field still opens with correct geometry. After `computeAll`, the shell then reports `Face 1 missing` and the body reverts to the extruded box.

Fusion 2706.1.17 does not recompute a feature when it opens a document. Truncated native journals and five persisted dirty-flag variants opened as the stale box with healthy timeline items. Only `computeAll` produced the feature geometry. The writer must therefore emit the solved journal for every state.

Native acceptance opens each Kit document without a recompute and compares it with a native API control built in the same session. It walks every rollback marker, runs `computeAll`, applies the driving parameter edits, exports, reopens and recomputes again. Each suite started and ended with no open document.

| Suite        | Families                                                               | Accepted cases |
| ------------ | ---------------------------------------------------------------------- | -------------- |
| Corners      | Fillet, chamfer, shell                                                 | 5 of 5         |
| Extrusions   | New, join, cut and intersect with every extent                         | 15 of 15       |
| Holes        | Simple and counterbore, blind and through                              | 4 of 4         |
| Patterns     | Offset plane, rectangular and circular patterns, mirror, hole grid     | 5 of 5         |
| Multi        | `MultiPocketPart`, `MultiDiscPart`                                     | 2 of 2         |
| Edges        | Two-distance and distance-angle chamfers, multi-edge corners           | 5 of 5         |
| Construction | Offset plane, edge axis, vertex point                                  | 2 of 2         |
| Revolves     | Full and partial revolves, revolve join and cut                        | 4 of 4         |
| Countersinks | Through and blind countersink holes                                    | 2 of 2         |
| Shells       | Shells with open side faces                                            | 2 of 2         |
| Moves        | Translation, turn about Z                                              | 2 of 2         |
| Offsets      | Top and side face offsets                                              | 4 of 4         |
| Drafts       | Outward and inward side drafts                                         | 3 of 3         |
| Bodies       | Second bodies, combines, splits, body patterns                         | 11 of 11       |
| Lofts        | Rectangle and circle lofts, loft as a second body                      | 3 of 3         |
| Sweeps       | Rectangle sweeps along bent and S-shaped paths, sweep as a second body | 4 of 4         |

`MultiPocketPart` combines a slot cut, a hole, a hole pattern, a fillet, a plane and a mirror. `MultiDiscPart` combines a disc, a pocket, a circular pattern and a counterbore. `CornerSetPart` and `ConstructionPart` add holes, corners, axes and points to a cut part.

Copy-body features are captured as [native family records](FamilyRecords.json.xz) only. The copy-body control uses `DcPasteBodies` and `DcReparentBodiesFeature`, which have no schema in the typed catalog.
