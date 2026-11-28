# Source-free Fusion cuboid research generator

The generator creates a new Fusion archive from a narrow semantic JSON request. It uses Kit's existing constrained cuboid constructor and writes a new archive once strict readback verifies the graph. The request names three independent drivers, the sketch, extrusion and body, and a linked generic physical material.

## Usage

Use the repository's Python 3.14 environment with its SDK on `PYTHONPATH`. Save a schema-1 request with this shape.

```json
{
  "schema": 1,
  "title": "Generated Cuboid",
  "dimensions_mm": {"width": 16.4, "depth": 27.1, "height": 13.8},
  "drivers": {"width": "blockWidth", "depth": "blockDepth", "height": "blockHeight"},
  "names": {"sketch": "Base Sketch", "extrude": "Boss", "body": "Block"},
  "material": {"label": "Block Material", "density_kg_m3": 1100, "rgba": [0.25, 0.5, 0.75, 1]}
}
```

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCuboidGeneration/GenerateSemantic.py Request.json Candidate.f3d --written-at 1795564800
```

Choose an unused `.f3d` destination. The command reports the exact request and candidate hashes. The output is deterministic for the same request and timestamp under the pinned runtime. The constructor uses a fixed logical archive name, so changing the destination basename does not change the bytes. Edit `dimensions_mm.height` for the extrusion height or `dimensions_mm.depth` for the rectangle's Y dimension. The destination must support same-directory no-clobber publication. A race between two fresh generator processes for one destination published exactly one verified candidate and left no temporary files. Its SHA-256 was `ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be`.

## Scope

The supported graph is one positive, origin-anchored XY rectangle with a separate fixed corner, four horizontal or vertical rules, two direct driving dimensions, and one positive one-sided extrusion. The named physical material includes its label, SI density and RGBA. No CAD application or model calls participate in generation.

This research constructor accepts authored requests. Preserving an existing saved graph's procedural texture mapping, visibility, camera, snapshot, configuration and previews requires additional rules. The baseline and separate JSON height-edit candidate passed fresh Fusion geometry and material lifecycle checks under the [oracle protocol](../../../../re/Fusion/SavedCuboidGeneration/GenerationOraclePlan.md). The independently authored control used a body color override where the candidate used material-linked appearance. Full presentation and held-out native acceptance remain open. The [saved cuboid reader](../../Fusion/Adapter/FusionSavedFixedCuboid.md) retains its read-only admission.

## Verification

The [scene geometry plan](../../../../re/Fusion/SavedCuboidGeneration/LeafPlanEvidence.md) derives the canonical physical face and edge roles from dimensions and checks them against actual constructor history. The [structural graphics probe](../../../../re/Fusion/SavedCuboidGeneration/SceneWireEvidence.md) binds those roles to the generated Design body and verifies exact typed graphics readback on three generated inputs. The [standalone snapshot probe](../../../../re/Fusion/SavedCuboidGeneration/PrismSnapshotEvidence.md) derives its closed solid and two tagged rectangular sheets from the generated Design graph and history. These isolated codec results leave archive-level graphics and snapshot ownership qualification open.

The [source-unavailable process probe](../../../../re/Fusion/SavedCuboidGeneration/ProbeSemantic.py) runs the constructor in a fresh process and checks the resulting strict document, complete typed state and exact written bytes. Run it with an unused output directory.

```powershell
python -B re/Fusion/SavedCuboidGeneration/ProbeSemantic.py --output ProbeOutput
```

All nine audited cases passed in 120.591 seconds with Python 3.14.6, SDK revision `f77ab6a0f49af7771ce1509edec5053454985cad` and producer SHA-256 `9376e46d309ba2729d82d4c930dd73e1e1843fcae51280aa5d1ae8f054941131`. The probe kept the test-owned original archive unavailable, recorded 13 distinct process audit handshakes, and verified byte-identical fresh baseline generation and public re-emission after persisted JSON readback. Separate height and rectangle-depth edits preserved the driver, naming, material and geometry contracts. Procedural material, an added source byte field, missing drivers and a source path were refused. An occupied destination retained its original contents. The report SHA-256 is `96f6da49cfb7dc30945fa6fcbab2127adef9615f9e4c263e562d1b6e6ebf8cd1`.

A 16.4 × 27.1 × 31.4 mm request with custom names, 1,100 kg/m³ density and four explicit color channels generated the same 100,196-byte archive in two fresh processes. Candidate SHA-256 was `213b3dd8145142056e3adc4d97567ce89b12c542c69775081c1cdcfe6a2f4282`. A separate request changed only the height to 23.25 mm. Strict readback measured the volume change from 13,955.416 to 10,333.23 mm³. Its candidate SHA-256 was `deb1b3039fd1f1f43ef359c97e76a023e944cc016fb80c37376ccb748361ce66`.

Those two fresh constructions prove the constructor can author the required fixed corner and driver graph from requested semantic fields. Their native record allocation differs from Fusion's saved-archive profile. The writer emits a candidate without self-attesting native measurements. The separate oracle binds each measurement to the actual candidate digest.
A separate holdout was selected after the producer source froze. The independently strict-read candidate preserves its named geometry and material through persisted JSON. Its exact SHA-256 is `f318fd94e17b42603c93135d9d6fde7691e5050f950edeee29d4be0d7a5d52b0`. The held-out check is offline. See the [request and native evidence bindings](../../../../re/Fusion/SavedCuboidGeneration/GenerationOraclePlan.md).
