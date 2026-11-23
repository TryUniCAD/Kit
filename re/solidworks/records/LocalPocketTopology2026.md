# Closed rectangular recess in a generated Parasolid local body

This is a scoped #121 import-construction prerequisite from aggregate
`3b5caa3b599b2184f32260e8b383d15044946d5f`. It advances the
[geometry fallback boundary](ImportedBodyFallbackBoundary2026.md) for a
single analytic rectangular pocket. The exit condition is complete typed
local and linked archive replay of independently authored geometry with
unchanged measured planar and periodic controls. Public publication needs
its own exact native lifecycle and strict readback under the
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).

## Native topology evidence

The two disclosed original and edited shell saves were authenticated against
[the earlier strict receipt](../measurements/2026/SdkColdShellCompile01.json).
The source record binds both files to 2026 SP05.2 build `34.5.2.0604` and
disclosed native controls, under source terminal receipt SHA-256
`d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b`.
[Build and source provenance](https://github.com/TryUniCAD/Kit/blob/15749182cdb3142fcab0fbe9719bea21d4a44ee7/re/solidworks/records/SavedOpenShellReader2026.md)

`ReadActiveNodes` consumes each complete active partition of schema
`SCH_3701250_37102_13006`. Live BODY 2 owns the single closed boundary.
FACE 41 has linked loops `62 → 195 → 0` in the original and `64 → 194 → 0`
after the edit. Each loop resolves to four owned fins and four distinct
terminal vertex points. Their signed XY areas are `+2173, −1677.96` mm²
and `+2173, −1559.2036` mm² respectively. The native plane carries negative
Z and the face sense reverses it. The two saves establish this particular
owner topology. [Loop ordering gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/PocketRimOwnsTwoLoops.md)

## Model-owned construction and verification

`MakeBareImport` routes a planar boundary with an inner loop to the
[local pocket compiler](../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/MakeLocalPocket.py).
The compiler checks one closed untransformed solid with three Z stations,
the complete directed rectangular outer and inset boundary, one outward
normal per effective face, and exact Cartesian plane incidence. The
outward canonical representation gives identical typed nodes to the
equivalent authored reversed face uses. The recessed volume is strictly
inside the exterior in X and Y, and the cavity floor is strictly between
the exterior caps. The shared allocator binds both rims to one actual face
and links the loops in the modeled order. The other ten faces have one loop.

The internal encoder admits the new graph explicitly. It requires the bare
11-face, 12-loop, 24-edge, 48-fin, 16-vertex inventory and checks the shared
face owner of both loops. Shape coordinates, node identities and links are
computed from the neutral B-rep. The constructor receives no native source,
bytes, offsets, or fields. The separate native observer records geometry
and numeric ownership only.

Run the [guarded proof](../../tooling/sw2026/imported_body_source/VerifyLocalPocket.py)
in the isolated checkout with the previously disclosed, checksum-pinned
source directory:

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/VerifyLocalPocket.py all \
  --disclosed-native-directory /path/to/OpenShellSource02/Disclosure
```

The [receipt](../measurements/2026/LocalPocketTopology01.json) separates
native topology observation, fresh neutral construction and checks of the
previously measured controls into three fresh processes. Each generated case
uses 167 resident nodes and twelve logical streams, including seven exact
typed replays. Both cases compare against an independently calculated box
volume, inner volume, surface area and centroid. The same-locator solid box
near each case differs in only the local body stream, which grows from
1688 to 2868 bytes and 1706 to 2875 bytes. Across the four historical control
archives the whole-file checks preserve all 48 stream fingerprints on the
classic zlib 1.2.12 runtime.

The stock-type planner still refuses the new solid before public writing.
Default strict pocket reading reports the existing single-loop boundary.
The typed research read verifies the new graph directly from the generated
container. Generated pockets have no native or held-out acceptance. No
parametric history is projected, or assigned a transfer claim, by this
geometry-only work.
