# Controlled SOLIDWORKS curve source authoring

`re/tooling/sw2026/AuthorCurves.py` authors an independent research corpus for
circle and arc sketches followed by blind boss extrusions. It is oracle tooling,
not a native-format writer. It does not read saved streams, captured field
programs, or vendor data tables. The neutral inputs are in
`re/tooling/sw2026/CurveSpecs.json`.
The [static curve construction record](../../../../re/solidworks/records/CurvedSketchConstruction2026.md)
keeps native class, topology and counter rules separate from pending authoring
and generated-output acceptance. No circle/arc writer has been implemented.

The specification contains 24 discovery cases, six held-out cases, and two
independent controls. Cases vary radius, arc sweep and direction, sketch plane,
extrusion direction, inner contours, disconnected contours, construction
geometry, and tangent capsules. The controls use a corner rectangle and a circle
created from a center and circumference point. They do not call the proposed
format writer. Native held-out files and streams must remain unavailable to
agents deriving or implementing the writer family. The held-out neutral inputs
and independent oracle measurements remain available for acceptance.

## Owner-controlled use

Only the oracle owner runs this tool. Stage reviewed copies of `AuthorCurves.py`,
`CurveSpecs.json`, `Swapp.py`, and `OracleIdentity.py` in one guest-accessible
research directory. Keep vendor software outside the checkout. Keep native
outputs outside the checkout. Supply the guest-visible repository root to the
output guard and use a new output directory for each batch. Do not run the tool
while another agent or user owns a SOLIDWORKS session.

For example, after staging the reviewed files:

```sh
prlctl exec "Windows 11" --current-user python "C:\KitOracle\Curves\AuthorCurves.py" "C:\KitOracle\Curves\CurveSpecs.json" "C:\KitOracle\CurveSources01" --checkout-root "\\Mac\Home\Documents\UniCAD\Kit" --generator-revision "<reviewed-source-commit>"
```

`--case NAME` may be repeated for a diagnostic subset. A subset never writes a
family lock, even when its selected cases pass. Exit code 0 means a complete
family lock was written; a successful diagnostic subset still exits with code 2.
Read its case, control, and first-failure records to distinguish successful
preflight from a failed native phase. `--timeout` sets each native
phase's wall-clock limit in seconds; its default is 240. A complete run uses two
fresh native phases for each control and source case, plus trailing control
verification. Account for application startup time when scheduling the batch.
The [managed-worktree staging boundary](../../../Gotchas/Conversion/Solidworks/Tracing/ManagedWorktreesNeedOracleStaging.md)
describes why the guest-visible staging directory and supplied source revision
must remain separate from the isolated checkout.

Each authoring and verification phase runs in its own Python worker and fresh
`SldWorks.Application.34` COM server. `OracleIdentity` must confirm executable
version `34.5.2.0604`, the pinned executable SHA-256, and x64 PE architecture
before a document is created or opened. Existing SOLIDWORKS processes prevent a
new phase. Normal cleanup exits only the owned session. After an abnormal worker
exit or timeout, the controller can terminate only a process whose recorded
identity matches that phase's exact oracle. Forced cleanup does not turn a
failure into a pass.

The input-dimension prompt preference is read before modification and restored
in `finally`. Both changes are read back; the application setter returns no
success status. The
[preference setter gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/PreferenceToggleSettersReturnNoStatus.md)
records the failed preflight that exposed this binding. Restoration or cleanup failures remain
failures. An abnormal native process termination can prevent restoration; the
partial record preserves its earlier value for the owner. The tool does not
claim restoration after a crash.

## Recorded evidence and lock conditions

Every native call has a persisted start record and its returned value or
exception. The first failure remains separate from later cleanup errors. Worker
stdout, stderr, process exit code, timeout state, and partial measurements remain
in the output directory. A failed phase stops later source cases, records them
as pending, and still attempts verification of healthy leading controls.

The tool checks actual return values for rebuild, save, selection, relation
creation, and dimension setting. It reads sketch geometry and relation state
back, records the recursive feature tree with errors, warnings, and suppression,
and reads the extrusion definition. It compares body count, volume, surface area,
and center of mass with formulas from the neutral profile. Position comparisons
use the native sketch transform. A fresh verification phase reopens the saved
source, changes its selected driving dimension, and checks the resulting
geometry. It closes that edit without saving and verifies that the original
source hash did not change.

The two leading controls must pass creation, reopen, and driving-dimension edit.
The trailing controls reopen those same unchanged native files in fresh
processes and repeat their checks. Any failed control invalidates the batch.
Native warning dialogs, unavailable queries, unsupported relation calls, failed
casts, missing driving dimensions, and unverified geometry prevent a lock.
Recorded native loading-progress windows remain separate from dismissed error
dialogs.

`Lock.json` is written only after all 30 specified source cases and both leading
and trailing controls pass. The lock records the source and manifest hashes,
discovery/held-out/control split, oracle identity, tool hashes, specification
hash, supplied source revision, and complete batch hash. It explicitly states
that curve writer implementation has not started. Locking an oracle-authored
corpus does not establish acceptance of any Kit-written output. No format writer
family may use these files or saved values as runtime input or generated output.

## API evidence and limitations

The wrapper uses the documented 2026
[relation creation API](https://help.solidworks.com/2026/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.isketchrelationmanager~addrelation.html),
[constraint types](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swConstraintType_e.html?id=1adf855f082744c0b4eb2dac2adea63b),
and [relation filters](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSketchRelationFilterType_e.html).
Fixed centers, coincident endpoints, tangent joins, and equal arc lengths use
their documented API enum values. Shared endpoint identity is recorded instead
of adding a redundant coincidence constraint.

The 2026
[dimension state enumeration](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swDimensionDrivenState_e.html)
defines driving state as 2. The wrapper requires that state and checks dimension
setter status and read-back values. The
[configuration scope](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSetValueInConfiguration_e.html)
is the current configuration. The
[blind end condition](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swEndConditions_e.html?id=db3cfc793dcc412a94c6e64da4c926a5)
is 0. Boss reversal is the third `FeatureExtrusion3` argument.

Some official 2026 circle, arc, and extrusion method pages returned only the web
help shell during preparation. Their installed dispatch interfaces, sketch
casts, relation bindings, arc orientation, dimension placement, and extrusion
read-back remain subject to the native phase checks. The implementation does not
substitute older-version behavior or assume these operations succeeded.

This tool does not implement ellipses, splines, arbitrary support planes,
equations, cuts, draft, thin extrusion, or other end conditions. It does not
establish a production writer, FCStd conversion coverage, or a donor-free native
file generator. Underdefined source sketches are accepted only if their declared
geometry, driving state, requested relations, and measured edit all pass; the
tool does not equate a successful API call with preserved design intent.

## Verification

The tool and neutral specifications were initially prepared without launching or
attaching to SOLIDWORKS. Static Python syntax parsing and JSON inspection passed. The
specification contains 24 discovery cases, six held-out cases, two controls, and
32 distinct names. The Python file contains no comments or docstrings. The first
controlled preflight on executable `34.5.2.0604` stopped both independent controls
before document creation because the wrapper treated the application's void
preference setter as a Boolean. The wrapper now requires preference read-back
instead. Relation and geometry read-back paths remain unverified until a later
native phase reaches them. No curve source family lock or generated curve
acceptance is established. No local tests were run.
