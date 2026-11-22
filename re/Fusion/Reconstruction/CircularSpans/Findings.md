# Circular extrusion extent records

The controls were authored through the licensed Fusion API on 2026-11-22. `Manifest.json` binds each archive hash to observed body dimensions, volume, surface area, timeline and model parameters. Original and held-out sets have different dimensions, circle centres and radii. Both sets contain unchanged healthy controls before and after the variant batch.

## Confirmed observations

- `directionType = 1` is one-sided, `2` is two-sided, and `3` is symmetric. `symmetricMeasurementType = 1` denotes full distance and `2` denotes distance per side, consistent with the existing `ExtrudeControl.py` grammar.
- A reverse extent stores a negative distance expression. It does not require `isFlipDirection = True`.
- Symmetric and two-sided cylinders can retain two operation groups on the same side face. Both groups must map back to the same owning feature. Their two far circular edges have the native `-1` label.
- A feature operation allocator can retain an additional unused operation ID. The held-out reverse cylinder allocates two IDs but its body progenitor and side tag use one. Allocated IDs and active geometry operation IDs must be validated separately.
- These cases use a typed `JournalModel` body and a `GeometryState` snapshot. The journal header scale is bookkeeping and differs from the snapshot scale. The coordinates in both parsed models remain centimetres.

## Confidence and scope

The observations above are confirmed on the recorded API-authored controls. Generalization outside the measured plain circular, untapered XY cases remains partial. Arbitrary history, arbitrary orientation and multi-feature projection are separate work. Native API authorship is not evidence that a decoded or converted output passes vendor acceptance.

## Reproduce

Run `cad-api script fusion CaptureControls.py --output UNUSED_DIRECTORY` or `CaptureHoldouts.py` through the private owner API. Each script exports controls and closes its documents. Decode each recorded archive with `kit decode FILE --output OUTPUT`. The integration replay invokes the public CLI in a separate process and compares its neutral bounds, volume and area to this manifest.
