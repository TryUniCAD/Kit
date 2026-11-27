# Strict reading of circular offset-start extrusions

## Behavior

The default Fusion SDK reader and `kit decode` now accept a bounded offset-start extrusion family.
The source must contain one identity-placed XY sketch with one unconstrained full circle, followed by one untapered NewBody extrusion with positive, unequal two-sided distance controls.
The native start definition must be ProfilePlane or the explicit OffsetStart type.
Positive, negative and zero start offsets retain a distinct owned `ProfileOffset` parameter.

The neutral `DistanceExtrude` definition references the first distance, second distance, start offset and both taper parameters separately.
All five parameters preserve their native role names, expressions, values and feature owner.
Lengths are millimeters and angles are radians.
The existing distance evaluator obtains the lower station as `offset - second` and upper station as `offset + first`.

Admission still requires complete reciprocal parameter ownership, unique allocation IDs, the original feature/component/body joins, current journal geometry, saved snapshot geometry, topology labels and native mass-cache agreement.
An offset scalar alone does not supply identity or qualify a solid.
The shared parameter binding validator moved into its own module without changing its existing contract.

## Usage

```python
from convert import open_document

Document = open_document("OffsetCylinder.f3d")
Definition = Document.feature_timeline[-1].definition
Offset = next(Parameter for Parameter in Document.parameters
              if Parameter.id == Definition.StartOffsetId)
print(Offset.value.value)
```

```sh
kit decode OffsetCylinder.f3d --output OffsetInspection.json
```

The command returns a neutral development report with `partial: false`.
The SDK document retains `fusion.read_only: true`.
In-memory typed JSON serialization remains available; native writing, interchange-file publication and `kit convert` remain guarded for this inspection-only family.
This reader extension does not qualify editable target conversion or a new writer route.

## Verification and remaining limits

The [qualification package](../../../../re/Fusion/OffsetAdmission20261127/README.md) pins the native input groups from [PR #395](https://github.com/TryUniCAD/Kit/pull/395).
The first deterministic candidate is `23be702fd32d3092d98974c725bcc9d3b95fe0ee`; its final binding decomposition is `7ce58d3962f89c5c184e1fd993126e4927f9d73d`.
The first background replay strictly read 109 of 139 native archives and retained 30 XZ/YZ placement refusals, with zero reader errors.
All 1,447 scope, owned-role, geometry and receipt comparisons passed against independently recorded native measurements.
Research output keeps its separate `kit.research_read_status: unqualified` marker.
The final pinned replay repeats those counts and comparisons; all sixteen prior circular-span controls retain identical neutral-document hashes against the fresh-main baseline.
The package retains both replays and the prior-corpus comparison with their documents and receipts.

SDK and CLI integration coverage uses fifteen measured baseline/edit/holdout controls.
Real encoded corruption cases cover start type, missing or aliased references, owners, reciprocal links, allocator IDs, units, role names, value copies, nonfinite values, taper, snapshot planes and labels.
Additional process checks preserve the CLI's no-output-on-refusal behavior and existing destination bytes during refused writes.
These cases join the existing shared test suite and merge-queue planner; no separate runner or unit tests were added.
The large-PR local integration run at `e1bd1b2a5dada493309f5b94e0f2a8b4561d4f30` passes all 64 cases: 52 new SDK/CLI/archive checks and twelve existing read-only export guards.
Its JUnit report and initial fixture repairs are retained in the qualification package.
See the [offset-label witness gotcha](../../../Gotchas/Conversion/Fusion/Testing/OffsetStartLabelWitnesses.md) and [nonfinite-fixture gotcha](../../../Gotchas/Conversion/Fusion/Testing/NonfiniteEntityFixtures.md).
Current-head hosted checks and configured approval remain required.

XZ/YZ and other placed frames, tapered offset starts, one-sided offset starts, modifying operations, general profiles, constraints and editable target acceptance remain outside this scope.
Same-generator parameter holdouts do not establish independent generator-lineage coverage or a broader vendor-version promise.
