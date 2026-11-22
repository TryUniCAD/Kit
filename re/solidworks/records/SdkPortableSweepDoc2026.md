# Portable Standard sweep ownership

`SweepFeature(PathSketchId)` is a typed interchange definition for a standard
sweep. Its `FeatureStep.sketch_id` selects the section. The neutral validator
requires both sketch IDs to exist and differ, and the ordinary interchange
JSON codec preserves the two links. Older steps without this definition continue through the established generic link checks.

`PlanSweepPart(document, target)` binds the actual source roles below before
the [typed SDK composer](SdkColdSweepPart2026.md) allocates an archive.

| Role | Required neutral owner |
| --- | --- |
| Swept solid | One active create step named `OrdinarySweptBoss`, one result body made by that step and one active independent `Default` configuration |
| Section | `SweepSection` on canonical Right, a full origin-centered circle, fixed center and one actual driving diameter `D1` |
| Path | `SweepPath` on canonical Front, one open positive origin-start quarter arc, fixed start, vertical center-to-start and horizontal end-to-center, with one driving radius `D1` |
| Physical density | A separate literal `Density` quantity in `kg/m3` owned by the sole unassigned result body |
| Unit and identity | Millimetre geometry and length values, the part's neutral name, and an explicit typed native target locator and clock |

The measured composer retains both editable D1 values on their actual sketch
owners and uses the same explicit physical density for the part and its
definition. The planner refuses catalog material, appearance, retained geometry,
configuration override, native provenance and unsupported modeling options. It
also refuses a sketch dimension that disagrees with its curve.

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/ProveSweepDocument.py
```

The [process evidence](../measurements/2026/SdkPortableSweepDoc01.json) pins six
fresh guarded workers at the original disclosed locators. It exercises neutral
JSON serialization and decoding, reordered neutral inventories, projection of
the actual owners, full byte equality with direct composition, and independent
typed archive inspection with three exact linked stream replays.
Both originals match the
[disclosed native-tested whole-file hashes](../measurements/2026/OrdinarySweepColdNativeDisclosed02.json).
Separate edits to each sketch leave the other driver and owner intact.
Every worker records zero runtime access attempts and eleven model refusals,
including dangling or aliased path links, wrong sketch and density ownership,
stale dimensions and ancillary semantics.

The evidence applies to the interchange definition and the internal SDK
projection. The earlier [native protocol](OrdinarySweepHeldoutEvaluation2026.md)
identifies its separately frozen research writer.
