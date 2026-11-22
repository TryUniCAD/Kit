# Bounded unconstrained prism recovery

This follow-up uses the discovery corpus from PR #263 and new native controls authored on the licensed Fusion host.
The base revision is `7a0a987ec2f1ab4099c839621a8e51d18bcfa872`.
It qualifies two narrow reader paths, not a writer or bidirectional conversion.

## Rule and retained checks

When the native sketch has neither geometric constraints nor linear dimensions, preserve that absence in the neutral sketch.
The extended paths require modeled millimeter units. They admit an ordinary negative-distance XY rectangle or a positive-distance YZ rectangle.
The existing signed literal parser handles the unconstrained negative distance and verifies its value against the saved parameter.
The established constrained reverse path retains its wrapped-literal requirement and all existing refusal checks.

Placement, reciprocal parameter ownership, complete profile structure, journal history, saved geometry, tags and mass caches still require validation.
The reader does not manufacture driving width or height dimensions from raw point coordinates.
Both new paths carry `fusion.read_only`; removing the marker cannot bypass independent native-state reprojection at the bridge.
Public native writing remains unqualified.

## Independently authored controls

`Controls/Unconstrained` contains four new API-saved archives: a healthy XY control before and after, a reverse XY prism, and a positive YZ prism.
They use 37 mm width, 23 mm height and 11 mm depth. Their native volume is 9,361 mm³.
Native body count, volume, surface area and center of mass are recorded in `UnconstrainedNative.json`.
Both new cases failed the baseline strict reader and passed the candidate reader.
Their neutral body count, volume, area and rectangular centroid agree with the native measurements.
Both public SDK and CLI reads agree, including two ordered features and the absence of fabricated sketch constraints.
The files were authored after the proposed rule; they were not used to derive its geometry or scalar layout.

`Controls/Constrained` retains seven further native controls and their explicit driving-parameter, constraint, feature and geometry inventories.
The XY controls and reverse XY case pass. Other placements retain their explicit baseline refusals.
These observations do not qualify arbitrary annotation placement, XZ frames or reverse-YZ bodies.
`CaptureUnconstrained.py`, `CaptureConstrained.py` and `CaptureDecimal.py` are the submitted owner-authored research scripts.
The constrained script uses the existing repository P03 helper functions. It contains no vendor software.
Run capture programs only through configured native research workers, which supply the `app` and `work` objects.
`Controls.json` binds the original native bytes and published measurement files to their hashes.

## Reproduce the integration evidence

Use Python 3.14 and the checked-out SDK on `PYTHONPATH`.
Select an unused output report:

```sh
PYTHONPATH=src python3 re/Fusion/RectangleRecovery/VerifyRecovery.py --output /tmp/RectangleRecovery.json
```

The process executes public CLI and SDK reads of real native controls.
It compares independent numerical measurements and checks both marker-present and marker-stripped write refusals.
It also rejects unsupported placements, inconsistent saved distance and unsupported display units at the real archive boundary.
The typed archive mutations are negative research inputs, not vendor-authored measurements or production donor data.
The complete shared test suite runs this process through `tests/Research/Archives/FusionState/RectangleRecoveryTests.py`.
No separate CI runner or test workflow is introduced.

The existing signed-state and datum process reports retain their original SHA-256 values:

- Signed state: `f69f6cb0fc689fea9186c0ca1058ae6aa8212d141c75e87cc655c76f70f828db`.
- Datum state: `8fb0b77a5d097c95119649ab550a3718b93f567d9652b8f6b40cc956cd1f65e2`.

The source fingerprint and actual replay results are retained in this directory's evidence reports when published.
Do not count a successful decode as complete semantic recovery or target-application acceptance.

## Native worker follow-up

SOLIDWORKS resumed after supported recovery and an instrumented canary, then lost its COM connection again.
The new capacity-one controller resource stopped further dispatch on the first new failure instead of exhausting every remaining case.
The failed case subsequently passed an instrumented retry while an interactive SOLIDWORKS instance existed.
This observation does not establish the crash's root cause or a permanent worker repair.
Native recovery and remaining SOLIDWORKS batches retain separate evidence and acceptance requirements.

Decimal controls use 16.2 × 23.7 × 6.3 mm dimensions. The pre-review reader rejected reverse XY and positive YZ after centimeter to millimeter round trips. Native bounds and curve tags now compare original Point3D endpoints, preserving exact geometry disagreement checks. Named reverse distance references remain outside this bounded literal path.

`Controls/Decimal` retains four further independent API controls and `DecimalNative.json` records their measurements. `DecimalComparison.json` retains the pre-repair refusals. `InitialIntegrationEvidence.json` preserves the first four-control checkpoint. The original 144-file replay remains in `ReplayEvidence.json`; the first rounding-repair replay finished at 72 strict successes and 72 explicit refusals; revision-bound corrections for intermediate source fingerprints must settle before final readiness.

The scoped repair passes all 13 existing native edited-prism controls in `DraftCompatibility.json`, including four drafted prisms. The shared recovery process includes those four drafted controls alongside eight holdouts and fourteen refusals.
