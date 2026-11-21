# Thin boss revolve and ordinary revolve cut source acquisition

Task `B04-SW2026-REVOLVE-FAMILIES`, PR #121. The PR takeover owns the
exact SOLIDWORKS 2026 SP05.2 oracle and the independent pre-writer locks.
This packet prepares source authoring and a static field trace on aggregate
`7650d76e40e8f9c555c3daf1b028fb191fb0200a`. Source and construction
acceptance need separate measurements.
[Earlier thin archive schema evidence](ThinRevolveArchive2026.md) ·
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Matched disclosed models

| Family | Cases | Distinguishing measurements |
| --- | --- | --- |
| Thin boss revolve | One Direction, Opposite Direction, Mid Plane and unequal Two Direction walls | One ordered open axial profile segment and a separate construction axis on Front. Signed radius limits, unequal live thickness controls, partial sweep, exact extrema and wall-direction COM state. |
| Ordinary revolve cut | Inner stock, outer stock and unrestricted | Two disjoint full annular stocks and one partial cut crossing both radial bands. Source body mark 1 selects either real stock. Body face ownership and separate mass properties distinguish the cut result from the untouched stock. |

The thin trials use the same radius, profile span, primary thickness and
ordinary angular end. The asymmetrical modes compare both predeclared
wall sides in discovery. The recorded side must agree across cases and
phases. A held-out asymmetrical case takes the calibrated sign as an
explicit input. Mid Plane derives symmetric radial limits from one total
requested thickness. Its live dimension must represent either that total
or one half with an exact, stable scale through the edit.

The cuts start with two separately authored full turns. Each cut opens
one radial carrier on each intersected stock within its axial extent.
Analytic checks subtract the intersected sector's volume and first
moment from each affected stock. For area they add the sector boundary
area minus twice the removed stock-carrier area. Each body's extrema,
topology and actual face owners are recorded. The unselected stock
retains its own geometry. Body marks are checked before insertion.
The cut definition then confirms the selected stock in its rollback
selection context. The unrestricted arm exercises both intersections
and the absence of a selected-body restriction.

The tool checks the actual selected construction line and canonical
plane. It records API arguments, the recursive feature tree, solid
names, measured bodies, actual display dimension type/name/value, and
the editable drivers. It changes the angle and every active wall
thickness one at a time. Each edit rebuilds and must match its independent
prediction before the derivative is saved and reopened in a fresh
process. The original is immutable across open and edit. The report
preserves failed phases and records the exact control status.

[Thin discovery spec](../v2026/corpus/revolve-family-models/RevolveThinDiscovery.json) ·
[Cut discovery spec](../v2026/corpus/revolve-family-models/RevolveCutDiscovery.json)

## Static boundaries on the licensed SP05.2 model module

The exact model DLL has SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`
and image base `0x4b140000`. The new receipt pins original file ranges and
the actual primary serializer slots. REA could bind the PE identity.
An existing Hopper lease for the same target blocked fresh deep queries.
The instruction claims below use the exact original image, named PE
exports and direct disassembly. The earlier build-bound serializer
trace remains applicable.
[Exact static receipt](../measurements/2026/RevolveFamilyStatic01.json)

- Thin feature constructor `0x4c38a7b0` calls the ordinary base
  `0x4c38aa40` at `0x4c38a813`. It constructs two
  `moDisplayDistanceDim_c` displays, using
  `ParallelPlaneDistanceDim_c` as the model dimension class at
  `0x4c38a858` and `0x4c38a8a3`. The side arguments are 3 and 4.
  The constructor attaches `moThinSpec_c` through feature `f8f0` at
  `0x4c38a917` and sets feature `f828` to 5 at `0x4c38a91e`.
  Its primary serializer at `0x4bb1e5f0` first uses ordinary revolve
  serialization and then writes the thin-spec reference.
- Exported thin-spec thickness getters at `0x4c6ef010` and
  `0x4c6ef000` read their live `f08` and `f10` display objects
  through virtual `+0x868`. The secondary setter at `0x4c6ef240`
  writes through `f10` and virtual `+0x860`. Named direct getters bind
  `f28` to direction, `f2c` to cap-ends state, `f30` to end thickness,
  and `f50` to add-bends state. The thin-spec body also serializes its
  other fields. The constructor at `0x4c6eeeb0` initializes both
  `f30/f38` to -2.0 and `f50/f54` to zero. Their retained native save
  values, the mapping from COM direction enums to saved `f28`, and the
  dynamic display-class and alias closure still require the source saves.
- The ordinary cut constructor at `0x4c389ee0` calls
  `moRevolution_c` at `0x4c389f15`, then installs its distinct primary
  and secondary vtables. Cut and ordinary boss share the primary
  serializer `0x4bb1e7a0`. The inherited `moAtomFeature_c` selected
  scope getter `0x4b2867d0` reads `f544`, the all-body getter
  `0x4b28d860` tests that word for zero and the setter at
  `0x4b2924f0` writes the same word. The next discovery decode must
  compare `f544/f548`, the real wrapper and producer alias, and the
  body-feature list `f780` on the three sources. Shared base field
  boundaries are established. The revolve cut selection contents
  remain unmeasured.

[Thin wall owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/ThinWallsUseDisplayOwners.md) ·
[Earlier exact selected cut scope](ThroughAllMultiStockArchive2026.md)

## Run and lock

On the host, `preflight` computes the independent predictions from the
tracked model specification. `plan` emits a Windows job with the exact
specification, pinned control and seven tool file hashes. The installed
type-library inventory binds `FeatureRevolve2` and
`IRevolveFeatureData2`. The worker also resolves the actual registered
SwConst 34.0 names for wall type, angle/linear display type, driving
state, selection types, body type and edit scope before launching.
[Feature creation](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ifeaturemanager~featurerevolve2.html) ·
[Wall type enumeration](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swThinWallType_e.html) ·
[Registered API inventory](../v2026/evidence/RevolveAndConstraintTypeLibrary.json)

```sh
spec=re/solidworks/v2026/corpus/revolve-family-models/RevolveThinDiscovery.json
python3.14 -B re/tooling/sw2026/AuthorRevolveFamilies.py preflight "$spec"
python3.14 -B re/tooling/sw2026/AuthorRevolveFamilies.py plan "$spec" \
  --guest-spec 'C:\KitThinSources\Tool\Spec.json' \
  --control 'C:\KitControls\Control.SLDPRT' --control-sha256 "$control_digest" \
  --output 'C:\KitThinSources\Raw' --publication 'C:\KitThinSources\Disclosed' \
  --checkout '\\Mac\Home\Documents\UniCAD\Kit' \
  --source-revision "$source_revision" --source-tree "$source_tree" > Job.json
```

Set `source_revision` to the committed tool revision and `source_tree`
to that revision's `src` tree ID. Stage the exact seven files named in
`Job.json`, the unchanged specification as `Spec.json`, and the job in
`C:\KitThinSources\Tool`. Use unused raw and publication paths. Keep the
native operator's known-good, hash-pinned control outside the checkout.
Start the Windows worker with the designated CPython and pywin32.

```sh
prlctl exec --current-user "Windows 11" 'C:\Path\To\python.exe' -B \
  'C:\KitThinSources\Tool\AuthorRevolveFamilies.py' run 'C:\KitThinSources\Tool\Job.json'
```

Use the Cut discovery spec and separate unused paths for the second
batch. Each group starts and ends with the same healthy native control.
The four thin cases require 14 unique processes, and the three cut cases
require 11. Use the existing host watchdog and wait for the completed
run before reading active phase reports.
[Atomic receipt handling](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Process/LiveReceiptReadsCanBlockReplacement.md)

When the disclosed assumptions are settled, the oracle owner privately
authors a separate `heldout` spec with at least two different geometries
per supported family. Stage the job, specification and raw capture under
local guest `C:\` with the same tool revision and a new root. The runner
publishes only a sanitized lock with aliases, checks and digests. Case
labels, raw files, edit records and specification values stay in guest
custody. Commit the lock before starting writer work. Decode and replay
the disclosed `Config-0` and `ResolvedFeatures` first, including the
thin dynamic dimension chains and the cut stock identity, and classify
the remaining fields against those sources.

Host preflight validated both deterministic model plans and static PE
ranges. All four thin discovery inputs completed 14 independent native
processes with both controls healthy, including separate live angle and
wall edits. The active first wall lies on the measured positive radial
side for the forward controls.
[Thin disclosure lock](../measurements/2026/RevolveThinDiscoverySourceLock01.json)

Four independent thin models covering the four witnessed wall modes
completed another 14 fresh native processes. The author independently
edited both live walls on the unequal case. The exact guest lock was
published before coding the thin writer. The native originals and
model parameters stay private until the writer and comparison are frozen.
[Pre-writer thin lock](../measurements/2026/RevolveThinHeldoutSourceLock01.json)

The first cut batch stopped while identifying the second stock sketch.
The earlier single-sketch helper classified the existing first stock
profile as a second candidate. Both native controls passed. The repaired
author binds the new profile by the difference from its previous live
feature inventory, then verifies the selected construction axis in that
profile.
[Original cut failure](../measurements/2026/RevolveCutDiscoveryFailed01.json) ·
[Profile feature discovery](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Process/MultipleAuthoredSketchFeatures.md)
