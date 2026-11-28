# Internal ordinary revolve preparation

This is an internal preparation boundary for the independently measured ordinary Front rectangular revolve. Public writer registration remains closed until original-source semantic equivalence is qualified. It generates each field from the neutral document and explicit writer settings, returns bytes and actual owners, and performs no file or CAD access.

## API and ownership

`convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve.PrepareRevolve(DocumentValue, TargetValue, WrittenAt, OptionsValue=None)` returns `RevolvePart`. `CanPrepRevolve` takes the same arguments and applies the same admission. `WrittenAt` is the explicit integer writer epoch used by the shared part recipe. The selected configuration must be the actual single configuration's ID or name. Existing shared options remain authoritative; unknown options reject.

A pathname target must satisfy the shared final-part-path rules and the actual modeled document basename. A named byte stream requires an explicit `WriteOptions.final_destination`; that exact Unicode pathname becomes the generated self-file identity. Neither entry reads or writes the destination. The I/O layer remains responsible for transactional output. `CanPrepRevolve` does not imply public registration or complete original-source acceptance.

`RevolvePart` contains the actual `PartSystem`, `ProfileGraph`, revolve feature, selected-axis reference, end owner, angle dimension graph, three headers, Definition/configuration/resolved graph snapshots, logical streams, complete bytes, `RevolvePlan` and `PartBuildInput`. `CurrentConfig` returns the actual first system configuration. No result is reconstructed from saved payloads.

For an explicitly prepared `PartBuildInput`, the lower boundary is `Archive.Construction.Revolves.Part.MakeRevPart.MakeRevPart(DocumentValue, InputValue)`. `ProjectRevolve` is the same strict neutral projection used by both boundaries. The shared `PartLabels` protocol supplies only actual name/configuration/support information to unchanged generic part helpers.

## Admitted source profile

The document is millimetre based with one configuration, canonical Front support at model origin, one sketch, one ordinary one-sided boss, one parameter and one selected construction line. The real contour has four axis-aligned edges strictly right of the separate upward local axis. Exactly four authored H/V contour relations are required; fixed state, axis anchoring and extra sketch drivers reject. The positive unexpressed `D1` parameter is in radians with `1e-8 < angle <= tau`. The neutral effective axis is +Y forward or -Y reverse, while the selected source line stays upward. Both full and partial angles are measured, and create/join operations preserve the exact admitted output.

Additional geometry, configuration, relation, feature, end, support, expression, material, property and named-body semantics reject. There is no cache, imported payload, template, captured value program, public dispatch change or acceptance flag.

## Reproduce the frozen proof

Use the parent-retained immutable root `SdkOrdinaryRevolvePrepare01`, whose `Source03.json`, `BaseSource01.json`, `ToolsFinal02.json` and `Inputs01.json` bind the complete two-source/tool/input closure. `RunPrepareProof02.py` verifies membership and hashes before execution, and requires a new output directory. With that root staged at `$revolve_root`:

```sh
.venv/bin/python -B "$revolve_root/RunPrepareProof02.py" --root "$revolve_root" --output "$unused_proof_output"
```

The stageable copy is [RunPrepareProof02.py](../../../../../re/tooling/sw2026/revolve/Preparation/RunPrepareProof02.py). It expects the frozen closure layout, rather than reading mutable checkout sources. The [sanitized measurement](../../../../../re/solidworks/measurements/2026/SdkRevolvePreparationProcess01.json) binds its report and exact manifests. The method runs 60 fresh processes: eight construction/preparation workers, 18 neutral rejection workers, eight option/path rejection workers, four existing-polygon baseline/layer workers and 22 native-state baseline/layer workers. Every positive runs after input bytes and imports are prepared, with extra runtime file/process/network/native-library access forbidden. It opens no original held-out source and launches no vendor process.

All four containers retain the native-measured hashes. Eleven generated, saved and disclosed control states produce 55 paired normal strict reader comparisons and 176 model-stream comparison visits in the pinned proof. That source snapshot records the prior Biography refusal. On the integrated SDK, twelve guarded preparation workers preserve the same bytes and option refusals. All eleven states pass 55 strict reader modes and byte-identical re-emission of the eight model streams, Biography and History. [Integrated replay](../../../../../re/solidworks/measurements/2026/SdkRevolveIntegration01.json)

## Revision boundaries

The 60-process writer proof pins the source before the separate cache-free revolve reader. Its generated default B-rep refusal is historical evidence for that closure. Current cache-free geometry qualification is tracked in [SdkColdRevolveGeometry01.json](../../../../../re/solidworks/measurements/2026/SdkColdRevolveGeometry01.json), outside this writer freeze. Cached native saves and disclosed controls pass strict geometry in the frozen comparison.

The initial support-name mismatch is preserved as a false 31-process report. Shared `CheckPartInput` is now called before reporting preparation support; actual constructor bytes never changed. See the [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Revolve/PreparationMustBindFinalNativeSelfName.md).

[Detailed record and exact source identities](../../../../../re/solidworks/records/SdkRevolvePreparation2026.md) · [Change entry](../../../../Changes/Solidworks/Construction/Revolve/SolidworksRevolvePreparation.md)
