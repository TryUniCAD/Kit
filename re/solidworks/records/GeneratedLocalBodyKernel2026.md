# Generate a bare local BODY transmit from neutral geometry

The research builder creates an ownerless Parasolid BODY in
`SCH_3701250_37102_13006` from one typed analytic B-rep in millimetres.
Its bare transmit header follows the [disclosed native BODY witness](ImportedLocalBodyKernel2026.md).
The two inputs below are independently authored neutral shapes. Construction
reads no CAD file and uses no CAD runtime.

## Admitted geometry

The [builder](../../tooling/sw2026/imported_body_source/BuildLocalBodyKernel.py)
requires one connected closed planar prism on two parallel XY levels. It
checks the input B-rep's topology and line trim endpoints, the oriented face
loops and the correspondence with the simple lower section. Each face uses
one outer loop, and each edge uses one exact line carrier. The accepted
profile has no source attributes, provenance, design-body links, nonidentity
body transforms, pcurves, wires or nonzero tolerances. Unexpected input
fails before emission.

The shared [prism projection](../../tooling/sw2026/para/rectangle/Geometry.py#L95)
builds the existing solid and void regions, shells, faces and fins. The bare
path passes no marks and has no WORLD. It creates the BODY with its owner
and attribute heads set to zero. The [topology completion](../../tooling/sw2026/para/rectangle/RectanglePartition.py#L77)
and checked index allocation supply every node, pointer and count. The bare
encoder requires a fully resident graph, verifies the region and shell
chains, and uses the same typed node renderer and measured compression frame
as the local-body witness.

The marked inputs retain the original branch. For both independent shapes,
their marked draft and completed topology compared equal to the function at
`01134e1e2582e42af1f60de71e8d609485e1f2db`.

## Guarded offline measurements

| Neutral shape | Vertices / edges / faces | Reachable nodes | Raw bytes | Wrapper bytes | Volume (mm³) | Area (mm²) | Centroid (mm) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Rectangular prism | 8 / 12 / 6 | 87 | 3759 | 1666 | 2574 | 1150 | (−2.5, 14, 8.5) |
| Concave prism | 12 / 18 / 8 | 125 | 5193 | 2231 | 5160 | 2068 | (6000/344, −1480/344, 3.5) |

Two distinct Python processes produced identical digests. The guard refused
file opens, directory enumeration, process or shell launch, socket events,
and dynamic-library loads during construction and verification. Its
successful runs observed zero such requests. A typed read recovers the full
geometry and re-emits each raw transmit byte for byte. An independent signed
tetrahedron sum over the decoded face loops checked volume and centroid. A
separate oriented-face sum checked area. Compression sizes and topology
differ with the input. The [numeric receipt](../measurements/2026/GeneratedLocalBodyKernel01.json)
records both neutral contours, measured values, raw and compressed digests,
and the owning source hashes.

## Reproduce the candidates

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/BuildLocalBodyKernel.py \
  --artifacts "$UNUSED_EXTERNAL_DIRECTORY"
```

The optional artifact directory must be outside the checkout. It receives one
raw `.x_b` and one `.frame` per case, after the guarded measurement. Omitting the
option prints the numeric receipt without creating payload files.

## Cold kernel observation

Use the versioned SOLIDWORKS 2026 SP05.2 COM oracle. First pass
[the temporary body save interface](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IBody2~Save.html)
and [the matching restore interface](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModeler~Restore.html)
on a known native solid with fresh processes. Also try the disclosed native
bare BODY byte stream from the same local payload profile. If both controls
pass under the same stream framing, restore each generated raw payload in an
independent process before opening any part or rebuilding. Record the
returned body type, temporary state, topology, mass properties and any
dialogue. Measure the native control again.

If the native bare stream needs an envelope, identify and verify that
envelope before judging the generated raw payload. The documented
[Parasolid exchange translator](https://help.solidworks.com/2026/English/SolidWorks/sldworks/c_parasolid_files.htm)
offers a separate check. Validate its COM import path first with a same-build
vendor-exported binary Parasolid file and the native bare-format control.
A verified exchange import establishes that import path's body result. The
embedded CArchive wrapper and imported feature still need their own native
comparison.

The recorded results are offline geometry and format evidence. Native
acceptance, imported feature construction and public conversion remain open.
