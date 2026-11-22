# Disclosed native save test for baked box tolerances

Task B04-SW2026-IMPORTED-BODY in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The comparison tests whether SOLIDWORKS 2026 SP05.2 uses two complete
generated BaseBody parts and keeps their populated local tolerance words
after a native save. Both independently disclosed FreeCAD files have one
literal standalone Part::Feature and the complete outward box boundary.
The live Part::Box has three owned driving lengths and is refused before
construction. [Source owner audit](../measurements/2026/DisclosedBakedFcstdOwners01.json)
and [typed transmit proof](../measurements/2026/DisclosedBakedLocalTolerance01.json).

The measured source supplies the configuration, labels, bounds, oriented
rings and one positive uniform length per face, edge and vertex. The
guarded worker gets only these typed model values and their custody
metadata. It computes a fresh neutral box, uses the shared part import,
header, scene and stream builders, and supplies the six face, twelve edge
and eight vertex nodes with the measured tolerance divided by 1000.
The complete local envelope and container are generated from typed nodes.
No saved stream or offset enters the writer. Two independent host
workers construct identical outputs with zero guarded runtime accesses.
Only Config-0-FeatureBodies/LocalBodies differs from the untoleranced
part generated at the same logical locator. Both kernels exactly match
the previously measured typed transmit. The two full containers also
resolve the actual feature and atom and reconstruct the six oriented
rings from the typed local group.

| Disclosed source | Generated part bytes | Generated SHA-256 |
| --- | ---: | --- |
| Baked01.FCStd | 9,910 | 5b4100d6c7f9b2e172337ced9c6c1d882dcac505ee8577414e8258c6028c9e83 |
| Baked02.FCStd | 9,895 | 448f35575f79d58e3154eba0f54d2eb151a2c6c2b0b23d1feb1126c6fffa8efc |

The exact encoded tolerance is binary64 0x1.b7cdfd9d7bdbap-34 m.
Each case starts from its generated logical locator and gets a separate
native save. There are six sequential fresh SOLIDWORKS processes.
The licensed bracket runs before and after both candidate lifecycles.
Each candidate records cold and rebuilt solid measurements, then saves
and reopens read-only in a fresh process. The native measurements cover
actual BaseBody ownership and ID, its one visible solid and six owned
faces, box incidence, volume, area, centroid and extrema. The previous
disclosed label experiment supplies a measured control for the first
source geometry and chosen label. [Prior label lifecycle](../measurements/2026/DisclosedBakedLabelNative01.json)

The typed saved audit binds the actual local group, rollback mark, atom
and final BaseBody. It reconstructs the outward rings and reports the
26 binary64 values by owner class. It distinguishes exact survival,
six-significant-figure survival, the original missing sentinel, changed
values, absent local group and an unresolved saved layout. A prior
independently native-saved rectangular control, SHA-256
6c3bd9562db256fcb79b467cadac754dd158a871081a6884fee2c56f62cd4f1b,
exercises the stored attribute grammar where the generated cold graph
has none. Its six faces, twelve edges and eight vertices all report the
missing sentinel. An absent
group does not qualify a tolerance elsewhere in the file. [Native saved
control evidence](../measurements/2026/ImportedLocalBodySdkSavedRead01.json)

This is a disclosed field and geometry comparison. Original FreeCAD
provenance, element map, appearance, intact conversion and held-out
qualification remain open. Registry behavior is unchanged.

## Reproduction

From the isolated method checkout, freeze the committed research-only
child of aggregate 8f02732268651f8d3123ab727c80ce813285323c.
The output directory must be fresh and separate from the three disclosed
originals. The control is used only by the oracle.

```sh
python3.14 -B re/tooling/sw2026/imported_body_source/BuildBakedTolerancePart.py stage \
  /Users/odin/Documents/UniCAD/Oracle121Takeover/FreeCADRuntime114/DisclosedSources01 \
  /Users/odin/Documents/UniCAD/Oracle121Takeover/ImportedBodySourceDisclosed03/Control.SLDPRT \
  /Users/odin/Documents/UniCAD/Oracle121Takeover/FreeCADRuntime114/NativeBakedTolerance01 \
  --revision FULL_METHOD_COMMIT
```

Run the observer serially using the oracle owner's measured current-user
Windows Python 3.12 and the exact Job SHA-256. The guest working folder
C:\KitBakedToleranceNative01 must be absent. Native records stay there.
The packet receives only the two authorized disclosed derivatives and
the native phase receipt. Exit 3 indicates an incomplete lifecycle.

```sh
prlctl exec --current-user 'Windows 11' py.exe -3.12 -E -B \
  '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\FreeCADRuntime114\NativeBakedTolerance01\Tools\ObserveBakedTolerancePart.py' \
  '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\FreeCADRuntime114\NativeBakedTolerance01\Job.json' \
  --job-sha256 JOB_SHA256
```

Use the returned Native.json SHA-256 to bind the separate host readback.
The output must be new. The audit does not run SOLIDWORKS.

```sh
python3.14 -B re/tooling/sw2026/imported_body_source/BuildBakedTolerancePart.py audit \
  /Users/odin/Documents/UniCAD/Oracle121Takeover/FreeCADRuntime114/NativeBakedTolerance01 \
  --job-sha256 JOB_SHA256 --native-sha256 NATIVE_SHA256 \
  --output /tmp/BakedToleranceSavedAudit01.json
```

[Build and audit](../../tooling/sw2026/imported_body_source/BuildBakedTolerancePart.py)
and [serial observer](../../tooling/sw2026/imported_body_source/ObserveBakedTolerancePart.py).
