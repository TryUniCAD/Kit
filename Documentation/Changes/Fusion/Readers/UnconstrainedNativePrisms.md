# Read bounded unconstrained native prisms

## Behavior

The strict Fusion reader now admits unconstrained millimeter XY reverse prisms and positive YZ rectangular prisms.
It preserves the source sketch's absent constraints and dimensions instead of inventing driving parameters.
The unconstrained path uses the existing signed-literal grammar. The constrained reverse path retains its previous literal contract.

Existing placement, ownership, profile, journal, snapshot, tag and mass checks remain active.
The new projections are read-only. Both ordinary native writes and marker-stripped native-state writes remain refused.

## Usage and evidence

Use `kit decode SOURCE.f3d -o REPORT.json` or the public strict SDK reader.
The [research package](../../../../re/Fusion/RectangleRecovery/README.md) retains eight independently authored controls and seven constrained comparison controls.
It records native geometry and parameter inventories, source hashes, replay commands and the process verification.
The new controls match native body count, volume, surface area and rectangular centroid.
The process verifies fourteen writer, malformed-input and unsupported-placement refusal cases.
Existing signed-state and datum process reports retain their exact recorded hashes.
The shared test suite includes the new process integration through its existing planner and shards.

## Limits

XZ placement, reverse YZ and broader constrained dimension annotations remain unsupported by this change.
Native writing, complete semantic qualification and editable cross-format conversion are not established.
The [authoring gotcha](../../../Gotchas/Conversion/Fusion/Readers/RectangleApiDoesNotSupplyDrivingDimensions.md) distinguishes coordinates from explicit driving dimensions.

The [launcher gotcha](../../../Gotchas/Research/Supervisor/Runtime/ShadowedKitLauncher.md) records a separate operational failure found during this work.
The repair selected the existing Python 3.14 installation explicitly. No process-fence implementation was weakened.

Decimal controls use 16.2 × 23.7 × 6.3 mm dimensions. The pre-review reader rejected reverse XY and positive YZ after centimeter to millimeter round trips. Native bounds and curve tags now compare original Point3D endpoints, preserving exact geometry disagreement checks. Named reverse distance references remain outside this bounded literal path.

Plain reverse admission is scoped to rectangular projection. Sixteen existing circular-span controls retain their previous grammar and pass native volume, area, bounding-box and parameter-role CLI comparisons.
