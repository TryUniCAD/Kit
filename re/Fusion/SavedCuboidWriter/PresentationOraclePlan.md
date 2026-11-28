# Saved cuboid presentation and edit acceptance

This plan measures the retained presentation of an unchanged saved cuboid and
the presentation and geometry after a deliberate Kit JSON height edit. Fusion
participates through its public API in a task-owned local oracle. The writer
runs offline. Inputs to the oracle are evidence and experimental controls.
See the [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md),
[writer model chapter](../../Playbook/WriterModel.md), and
[Fusion donor ban](../../../Documentation/Reference/Research/FusionDonorBan.md).

## Evidence already available

The [readiness record](../LocalOracle/SavedCuboidRoundTrip/Readiness.md) binds
each saved source, experimental lower-codec replay, and older independently
authored geometric control. The prior [native receipts](../EncoderRoundTrip/NativeEvidence.md)
ran on Fusion 2706.1.17. They establish the load, rebuild, edit, restore, save,
and reopen behavior of the earlier encoder outputs, with a different candidate
digest in every bracket. They record mass, density and the displayed material
name. The independent controls used Steel at 0.00785 kg/cm³. The earlier
candidate and reopened exports used Kit Generic Material at 0.001 kg/cm³.
Those controls establish oracle and geometry health for their brackets.

| Prior case | Geometry at source, mm | Saved source SHA-256 | Persisted JSON SHA-256 | Experimental unchanged replay SHA-256 |
| --- | --- | --- | --- | --- |
| Baseline | 16.4 × 27.1 × 13.8 | `b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752` | `e8ed6e2b9d96c54e2fc6f7008ce2b49b0cb162d21a2d13938169cb3f81a5c38a` | `c05251997755d8c68a0e8ba14db5ccf248a6ca5b1a610434f51a9801b4d0ce32` |
| Historical holdout | 43.7 × 12.9 × 31.4 | `5e4552d013a46a603f315fb904cfc62e34c359f1ed9daff51bddd09e3a63eeb7` | `2e0a2ca6821adc77d1cc18218571b71211c38ace56a53df86bd911689739b6b2` | `3fba656e80d6a426e0f62908079814df84087cbed5cbb64fae8776cc2b4aa405` |

Both replay pairs have full lower-codec typed model equality, including a
72-object graphics scene, one material part, one snapshot, the configuration
records, and byte-identical `Previews/big.png` (1024 × 1024) and
`Previews/small.png` (256 × 256). Both independent controls and earlier
edited exports differ from their restored source in the raw typed graphics,
material, and preview values. Raw equality against such exports would confound
save history and authored semantics. The exact unchanged replays above have
no fresh native measurements. The new JSON height candidate, matching-style
reference archives, appearance and camera records, renders, and held-out
qualification slots are pending.

## Inputs and controls

Prepare separate unchanged and JSON-height roles. Record the SHA-256 of the
original archive, strict persisted JSON, strict reload/rebuild inputs,
candidate, each control archive, and every oracle script and configuration.
Record the exact SDK revision, target Fusion build, role, dimensions and units,
parameter name, expressions, and expected fixed-corner mechanism. Generate
each candidate from the reloaded input in a new process with the native
source unavailable. Reopen the result strictly and compare the complete
authored and typed state with the planned role. Reject unsupported
dependencies before publication. Verify the input and
candidate hashes before and after the oracle. Record `dropped` and every
unsupported or missing observation.

Let `h0` be the original source height, `h1` the candidate height, and `h2`
the independent native edit height. For the unchanged role set `h1 = h0`.
For the baseline JSON-edit role use `h0 = 13.8 mm`, `h1 = 22.6 mm`, and
`h2 = 28.3 mm`. These values are qualification inputs, with only the unchanged
replay digest available above. Freeze the writer rules and tolerances before
selecting a new held-out combination of widths, depths, heights, and
presentation values. The historical holdout above is already visible to
writer development.

Author controls from a new parametric document through the public API at
`h0`, `h1`, and `h2`. Give the equivalent controls the same physical
material, resolved appearance properties, affected face/body assignment,
visibility and camera state as the case under test. Prove appearance matching
using property IDs, values and unit declarations. Retain the source archive
read as a second reference for its own stored values and reported asset IDs.
An independently authored equivalent appearance can have a different
generated identifier. Compare its resolved properties and the type and role
of each corresponding assignment. Keep the existing independent geometric
controls for harness health. Use
the [material observation precedent](../LocalOracle/AcceptChangedMaterials.py)
and the [documented appearance lookup workaround](../../../Documentation/Gotchas/Conversion/Fusion/Api/AppearanceLookupThrows.md).

Prepare separate one-factor controls with a camera change, a body visibility
change and a distinct face appearance. Choose colors or transparency with a
visible difference at fixed camera and geometry. Include a repeated unchanged
local export and a height-only change with style held fixed. Record each
control's independent authoring inputs and export mode. Use the existing
[capture preparation](../LocalOracle/SavedCuboidRoundTrip/README.md) for its
anchor and auxiliary controls. The camera, visibility and appearance controls
must produce the expected distinguishable observations before measuring
candidates. They test the oracle's sensitivity.

## Fresh-process bracket

Run each role on one Fusion build in this order. Start a distinct task-owned
Fusion process for each numbered stage. Record process ID and creation time,
owner/session identity, exact input digests, build, UTC timestamps, dialog and
error observations, and zero open documents at entry and exit. Each stage
closes every document it owns. Run the existing
[encoder measurement](../LocalOracle/EncoderRoundTrip/README.md) for topology,
history, parameters and geometry, and add the observations below.

The standalone [public API observation helper](ObservePresentation.py)
returns loaded camera, visibility, body and face assignments, and asset
properties for the current root cuboid. Pass the active viewport and the
design already opened by the capture stage to
`observe_loaded_presentation(viewport, design)`, before any viewport or
rebuild changes. Keep entries marked `unavailable` in the receipt. The
helper reads the current state and leaves opening, rebuild, render, export
and receipt publication to the existing oracle. Native execution of the
helper is pending a task-owned Fusion session.

1. **Control before.** Import the pinned independently authored control,
   record loaded state, rebuild, and measure. Compare its saved and loaded
   state to its authoring specification. Qualify the repeatability and
   sensitivity of the presentation controls before opening the candidate.
2. **Exact saved source.** Import the original vendor-saved bytes. Record
   camera before viewport changes or rebuild, then measure presentation and
   geometry both as loaded and rebuilt. The geometry reference here is
   `h0`. Preserve the source digest and use its observed appearance,
   visibility and camera state as source-side expectations.
3. **Candidate.** Open the exact generated bytes at `h1` without repair.
   Record loaded state, rebuild and measure. Change only `kitHeight` to
   `h2`, rebuild, measure and export locally. Restore its `h1` expression,
   rebuild, measure and export locally to a different file. Record both export
   digests. Restore any fixed test camera before export and record the
   restoration so the measurement itself does not become an authored change.
4. **Reopen.** Import the exact two exports from stage 3, one at a time,
   in this new Fusion process. Compare geometry, state, and loaded and
   rebuilt presentation with the expected `h2` and `h1` cases. In a separate
   offline SDK process, strict-read both exports and compare their states
   with the expected model. Any unavailable verification remains open.
5. **Control after.** Repeat the independent control on the same frozen build
   and capture settings. A failed control, mismatched digest, or incomplete
   process identity invalidates the batch.

Require the named parameter and its expression and units to agree with the
blind extrusion extent. Require a live fixed-corner rectangle, two named
driving sketch dimensions, healthy timeline and one solid with six faces
in each state. For positive origin-aligned extent at `h`, in millimetres,
require volume `w*d*h`, center of mass `(w/2,d/2,h/2)`, area
`2*(w*d + w*h + d*h)`, unchanged XY bounds, and Z bounds `[0,h]`.
After changing height by `dh`, require volume and Z-center changes of
`w*d*dh` and `dh/2`. Compare mass to volume times the selected physical
density, after unit conversion. Use the existing geometry harness's numeric
tolerances and record their values and units in the batch manifest.

## Presentation observations and comparisons

**Loaded state.** Before changing view, record camera eye, target and up
vector, projection type and orthographic extents or perspective angle.
Record occurrence, sketch and body visibility where applicable, including
effective visibility and independent lightbulb state. Enumerate the effective
body material, its assigned appearance and the body's appearance source type.
Enumerate each face's effective appearance and source type. Match the six
faces by outward normal and plane location against the cuboid, since face
indices and entity tokens can change across rebuilds. Record property IDs,
types, values, units and any connected resources for the resolved material
and appearance assets. Keep the exact typed source fields alongside rounded,
localized or normalized API values. A property or connected resource the
oracle cannot inspect remains unavailable.
[Camera API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Camera.htm)
· [body API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_BRepBody.htm)
· [face API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_BRepFace.htm)

**Viewport.** After measuring loaded state, export a front and an isometric
view into private scratch. Use the same explicit projection, orientation,
world-space scale, crop, resolution, background, display mode and lighting
for reference, controls and candidate. Record active preferences and the
camera actually used. Compute foreground area, bounding box, silhouette
overlap and region colors on corresponding face interiors. Verify the
hidden-body negative against a background-only render. Require at least two
same-state captures in separate healthy sessions to establish repeat noise.
Freeze per-metric bounds from the repeat spread and measurement resolution
before measuring candidates. The bounds must distinguish the one-factor
controls and reject the stale-height silhouette. If repeats overlap the
positive or negative controls, the metric has no acceptance threshold for
that run. Preserve image dimensions and hashes to bind the artifacts.
[Viewport export API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Viewport_saveAsImageFileWithOptions.htm)

**Archived preview.** Decode the preview members separately from any viewport
export. Record the member roster and ownership, each PNG's raw SHA-256,
decoded dimensions, and canonical decoded pixel digest. Check exact member
and pixel preservation for an unchanged replay where the input has previews.
For an edited image compare foreground and the height-sensitive silhouette
with the independent `h1` export under known framing. Preserve authored
presentation while requiring geometry-dependent scene, snapshot and preview
values to depict the requested height. Record archive modes with empty or
partial preview sets separately. The public viewport API renders the current
view and the DataFile thumbnail is obtained from the cloud. The local
archive check establishes embedded content. It does not measure a Fusion UI
surface reading that local PNG.
[Saved preview gotcha](../../../Documentation/Gotchas/Conversion/Fusion/Assembly/FusionSavedPreviews.md)
· [DataFile API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFile.htm)

**Typed writer boundary.** Check complete lossless custody for the unchanged
case and compare the edited model with an independently authored target
shape. Validate graphics world, object, mesh and style references, actual
placement and bounds, body and face material bindings, physical and
appearance values, snapshot geometry and preview dimensions and pixels.
Check the documented owner and unit of each changed value. Include
structurally valid stale-height graphics and preview, wrong-face appearance,
and incorrect material controls that cannot pass merely because counts and
references resolve. Refuse an unsupported presentation or dependency before
publishing any output.

## Status and handoff

Publish a presentation pass only when the exact-role bracket passes its
healthy controls, both fresh open and rebuild comparisons, the native
height-edit and restore checks, and offline archive comparisons. Report a
candidate failure separately from an invalid control bracket or an
unavailable measurement. The current artifacts establish offline typed
custody for two exact replay digests. No new native acceptance is recorded
for the replay or edit role.

The Windows [launch readiness record](../LocalOracle/SavedCuboidRoundTrip/Readiness.md)
records unrelated Fusion processes and an unmet idle guard. Wait for an
owner-confirmed isolated slot. The existing capacity-one supervisor
serializes configured participants, and its occupancy report measures
controller claims. It cannot certify physical readiness for unrelated
Fusion sessions. The documented Windows Phase A owner opt-in and private
endpoint do not establish deployment of this custom cross-process oracle.
See [supervisor occupancy](../../../Documentation/Reference/Research/ResearchSupervisor.md#recorded-claim-occupancy)
and [Windows Phase A admission](../../../Documentation/Changes/Research/Workers/WindowsFusionPhaseA.md).
