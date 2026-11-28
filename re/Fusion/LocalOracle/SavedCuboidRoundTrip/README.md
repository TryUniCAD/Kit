# Saved Fusion cuboid controls

These are local Fusion API research captures. They do not use any existing CAD
document as an authoring template and do not save to a cloud project.
The control keeps Fusion's assigned root component name. See the
[unsaved root component gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Api/UnsavedRootComponentName.md).

Use a private scratch directory and a fresh task-owned Fusion process for each
group. Check that the host has no other Fusion session before starting. On
Windows, use the installed Autodesk Fusion desktop shortcut. The repository's
[locked local bridge](../RunLocked.mjs) dispatches the prepared script.

```text
python re/Fusion/LocalOracle/SavedCuboidRoundTrip/Prepare.py anchor PATH/Anchor
node re/Fusion/LocalOracle/RunLocked.mjs PATH/Anchor/Run.py --timeout 90
python re/Fusion/LocalOracle/SavedCuboidRoundTrip/Prepare.py auxiliary PATH/Auxiliary
node re/Fusion/LocalOracle/RunLocked.mjs PATH/Auxiliary/Run.py --timeout 90
```

The anchor group holds the 18.7 × 24.9 × 11.3 mm dimensions constant across
separately authored designs. It captures a fixed corner at the origin position,
an explicit corner-to-origin coincidence, and a free corner with the same
coordinates. The translated fixed-corner control probes the origin boundary.
All cases retain the four axis rules and the two driving dimensions.

The auxiliary group starts with the fixed-corner design. It exports twice
without changing the authored model, then captures a camera-only change, a
body visibility change with the original camera, and an isolated height edit
with the body visible again. Compare the typed Design, snapshot, scene,
material, and configuration data separately. These comparisons can identify
related fields. They do not prove that a companion can be omitted from output.

The holdout group takes two privately selected dimension sets and independent
height edits. Provide two `--holdout` values in
`name,width,depth,height,edited_height` order, with dimensions in millimetres.
Withhold these archives and observations from rule derivation. Release them
after the reader admission rule is fixed.

Each group independently authors a known cuboid and uses its local archive as
the before and after control. `Capture.json` binds the request and script
digests, application build, process ID, UTC timestamps, and elapsed time.
The measurements include sketch points and their identities within one API
session, the actual anchor and operand relationships, dimension expressions,
the extrusion's driving reference, timeline health, and body geometry.
Each archive record gives the SHA-256 and lists all members with lengths and
CRC values. Fusion reads stored lengths in centimetres, angles in radians,
and volume in cubic centimetres.

Read both control observations and the final document count before using a
batch. Failed or missing native measurements remain incomplete. Candidate
acceptance requires separate fresh-process runs on the exact generated
archives, with independent controls before and after.

## Replay an existing native candidate

Use the source, candidate, and previously authored independent control digests
from the [readiness record](Readiness.md). The preparer checks each input
before staging the existing encoder oracle's four stages.

```text
python re/Fusion/LocalOracle/SavedCuboidRoundTrip/PrepareReplay.py baseline PATH/Replay --role reconstruction \
  --source PATH/source.f3d --source-sha256 SOURCE_SHA \
  --candidate PATH/candidate.f3d --candidate-sha256 CANDIDATE_SHA \
  --control PATH/control.f3d --control-sha256 CONTROL_SHA
```

Run `ControlBefore`, `Candidate`, `Reopen`, and `ControlAfter` in order
with the [encoder measurement procedure](../EncoderRoundTrip/README.md).
Start a new task-owned process for each stage. The first and last stages use
the same independently authored control archive. This local replay path
measures the identified research output only.

## Generated and native-resaved observer control

[GeneratedResaveEdited.f3d](Controls/GeneratedResaveEdited.f3d) is
the actual Fusion 2706.1.17 archive saved from the independently
generated no-OGS baseline after changing `riseGauge` from `8.875 mm`
to `27.875 mm`. Its SHA-256 is
`22128494045f7a9adb1e9eed7e1a95aeab06f067dea371c27981333b72d23968`.

The [authored request](Controls/GeneratedResaveRequest.json)
and [custody record](Controls/GeneratedResaveCustody.json) bind
the original source-free candidate, exact native save and fresh
native reopen. The normal integration suite reads this unchanged
fixture without a Fusion runtime. It exercises a saved parameter
observer order that differs from the parameter creation order.
This fixture is a reader control. Public writer acceptance for
saved documents retains its independent requirements.
