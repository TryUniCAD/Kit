# Bounded Fusion encoder round trip

The integrated CLI's reconstructed and edited cuboid candidates passed fresh-process native measurements in Fusion 2706.1.17.
Two separately generated edited candidates also passed on the same build.
The complete [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md) remain required.

## Behavior

Task `A11c` delivers this bounded research integration.
The [Fusion research adapter](../../../re/automation/EncoderRoundTrip/Fusion.py) exercises the existing qualified public adapter through persisted neutral JSON.
Its bounded model is one constrained XY rectangle and one positive blind cuboid extrusion.
The graph includes user parameters, dependent model parameters, sketch dimensions, constraints, analytic topology, and a material.

The adapter can reconstruct its supported authored graph and its equivalent strict native-state graph.
A driving extrusion-depth edit rebuilds the complete supported graph through `MakeFusionDoc` and a changed `DocumentSpec`.
It does not change only the visible parameter value.
The authoring specification, dependent parameters, geometry, and generated native state must agree.

Fixed native locator and timestamp inputs make candidate generation reproducible.
The existing public writer remains responsible for the native encoding and strict contract checks.
The research adapter does not weaken those production guards.
It does not use an AI service or invoke Fusion during generation.

## Usage

Use the repository's pinned Python 3.14 environment.
Run the boundary smoke from a trusted checkout containing this change.
Choose an unused output directory.

```powershell
python re/Fusion/EncoderRoundTrip/BoundarySmoke.py --root . --output .rescratch/FusionEncoderBoundary
```

The smoke creates its source graph without a vendor archive.
It persists neutral JSON, generates native candidates, and reopens them with the default strict SDK reader.
`Report.json` records deterministic observations, adapter and script hashes, and explicit unmeasured native acceptance.

The adapter returns candidate bytes to the shared research runner.
Destination safety belongs to that runner's process boundary.
The Fusion-only smoke does not qualify destination publication behavior.

## Limits

Only the documented cuboid family and driving extrusion-depth edit are in scope.
Additional features, unsupported edits, inconsistent contracts, and unqualified native states must fail explicitly.
Historical JSON remains subject to the public reader and writer contracts.
An omitted material collection does not authorize loss of the cuboid material.

The adapter validates the complete typed native state before reconstruction or editing.
It requires equivalence to the supported constructor graph, including previews and container data.
Only recognized generated identities and validated provenance fields can differ.
It then emits a new source-free candidate with a complete, consistent native contract.
Dropping native metadata is not an edit strategy.
The [contract guidance](../../Gotchas/Conversion/Fusion/Api/FusionSemanticContracts.md) continues to apply.
The [constructor-equivalence gotcha](../../Gotchas/Conversion/Fusion/Api/FusionEncoderConstructorEquivalence.md) explains the stricter encoder admission boundary.

The output is generated through the existing field-based codecs.
The new research path does not load a donor archive, captured payload, or vendor runtime.
These source inspections do not replace held-out native acceptance or the complete production donor audit.

## Verification

The [boundary smoke](../../../re/Fusion/EncoderRoundTrip/BoundarySmoke.py) exercises actual SDK serialization and native archive boundaries.
Its scope includes fixed-input reproducibility, strict native reconstruction, a driving edit, unsupported contracts, and historical JSON.

The [boundary evidence](../../../re/Fusion/EncoderRoundTrip/BoundaryEvidence.md) records 17 passing checks on native Windows with Python 3.14.6.
It binds the unchanged adapter and smoke source hashes to the retained report.
The strict SDK projection reports one solid, two features, one sketch, and seven parameters.
The driving edit changes volume from 12870.65625 to 17481.796875 mm³.
The profile is 17.25 by 23.5 mm.
The extrusion depth changes from 31.75 to 43.125 mm.
Fresh-process native open, edit, rebuild, save, and reopen measurements remain separate evidence.
The [native measurement record](../../../re/Fusion/EncoderRoundTrip/NativeEvidence.md) binds each measured candidate to its exact source and receipt hashes.
Independent Fusion controls passed before and after each candidate.
The receipt projector checks the candidate archive hash and verifies both saved archive hashes again at fresh-process reopen.
The strict SDK reader refused variants that Fusion saved after the native edits and restorations.
Admission of those saved variants requires reader work.
The [Windows oracle startup record](../../Gotchas/Conversion/Fusion/Api/FusionWindowsOracleStartup.md) describes the observed launcher and process behavior.
PR checks and merge-group acceptance also remain separate gates.

The earlier [public adapter evidence](../Fusion/Adapter/FusionPublicAdapter.md) describes its own artifacts and measured revision.
It does not qualify new candidates or this workflow revision automatically.
