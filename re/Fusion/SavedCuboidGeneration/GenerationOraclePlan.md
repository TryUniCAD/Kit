# Native oracle for archive-free cuboid generation

The generation input is a persisted semantic request. Each native control starts
from a new blank Fusion design and uses the same dimensions, labels, driver
roles, material density and color. The control archives stay in private
measurement storage and are never inputs to the generator. See the [CAD success
criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md),
[writer model chapter](../../Playbook/WriterModel.md) and
[Fusion donor ban](../../../Documentation/Reference/Research/FusionDonorBan.md).

## What the earlier native evidence covers

Fusion 2706.1.17 measured exact lower-codec replay
`c05251997755d8c68a0e8ba14db5ccf248a6ca5b1a610434f51a9801b4d0ce32`
through four fresh processes. It opened, rebuilt, edited, saved and reopened.
That replay began with a vendor archive's own typed state. The independently
authored geometric control used Steel at 7,850 kg/m³, and the replay displayed
Kit Generic Material at 1,000 kg/m³. Those measurements establish one replay's
geometry and edit lifecycle. The archive-free generator needs independent
measurements on its own exact output digests and on controls with matching
requested material properties.
[Earlier native evidence](../SavedCuboidWriter/NativeSameSourceReplay.md)

## Prepare independent cases

Use the generator's schema-1 JSON request. It contains `title`,
`dimensions_mm.{width,depth,height}`, `drivers.{width,depth,height}`,
`names.{sketch,extrude,body}` and
`material.{label,density_kg_m3,rgba}`. Keep the local receipt sidecar separate
from that request. Record the request digest, generator revision and producer
hash, deterministic epoch, candidate digest, case role, and the chosen native
driver edits. The verifier retains the exact SDK strict-read result and
document/native-state equality after durable JSON. Use those exact artifacts
when preparing the stage runners.

Generate and bind the public baseline first. For the deliberate JSON-edit
variant, vary only the authored height, generate an independent archive from
the edited JSON in a new process, and bind the second request and candidate
digests separately. Select at least one held-out non-square cuboid, with
distinct driver names, dimensions, density and RGB channels, after the
generation rules freeze. Preserve the holdout selection separately from
builder inputs. Use exact 8-bit channel fractions with opaque alpha for the
first material comparison. Declare the local Fusion build and SDK revision
for every batch.

The public baseline and edited requests are staged separately under
`.rescratch/FusionSavedCuboidGenerationOracle01`. Both use a 21.3 × 33.2 mm
rectangle, material label “Independent Opaque Baseline”, density 1,175 kg/m³,
and RGBA `[65,124,201,255]/255`. The control and candidate native height edit
target is 32.6 mm from either starting height. The optional independent width
and depth edit targets are 26.8 and 19.1 mm, respectively.

| Role | Height | Volume, mm³ | Analytic mass, kg | Request SHA-256 | Candidate SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| Baseline | 15.9 mm | 11,243.844 | 0.0132115167 | `a1955993a20f4e1edbc7b7bfb7ade0997ce25d900c1a46582cfb07779b55277c` | `ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be` |
| JSON height edit | 24.7 mm | 17,466.852 | 0.0205235511 | `e7014ed197a66ebe1cbe574e26ff457069a5d892f0076d965db3fce259bccc1a` | `8a28cf09b4e48108ca475d468b9e477314b92dfe1dedbf0715920ab0712682e3` |

Both CLI runs used epoch `1795564800` and producer SHA-256
`9376e46d309ba2729d82d4c930dd73e1e1843fcae51280aa5d1ae8f054941131`.
Each archive matches the separately emitted preflight bytes. The SDK
strict-read each preflight and round-tripped the neutral document through
JSON with equality. Those observations establish deterministic fixture
custody for native measurement. They supply no Fusion acceptance.

After the producer digest froze, the oracle independently selected a fresh
private holdout and ran the same CLI. Its request SHA-256 is
`c36e7157531b9106ffad9c713258ffd6fbc308c564c33711320432fbe3fdbde5`;
its candidate SHA-256 is
`f318fd94e17b42603c93135d9d6fde7691e5050f950edeee29d4be0d7a5d52b0`.
A separate strict SDK process verified topology, analytic volume and bounds,
named driver references, material label, density and RGBA, and decoded
native-state equality after persisted JSON. The native graph retains distinct
fixed corner and sketch origin identities. The authored neutral sketch
exposes the fixed corner, with the separate origin retained in native state.
The selection and measurements remain in private staging pending native run.

The [control helper](AuthorGenerationControl.py) accepts a newly created blank
Fusion document, the read request and an optional native material selected by
its public ID. Its geometry uses a separate, fixed lower-left sketch point,
the sketch's distinct origin, two horizontal and two vertical lines with
orientation rules, two dimensions bound to the named width and depth drivers,
and a positive one-sided extrusion bound to the height driver. Use the same
height at candidate open and before-control open. No control reads a generated
candidate or reuses another CAD archive during authoring. Set the request title
on the unsaved document through its public name property. Record the observed
root component name without assigning it directly.
[Document name](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Document_name.htm)

A blank design's current physical material provides an independent seed
when no explicit seed is supplied. Copy it into that owned design and assign
the copy to the body. Prefer a documented opaque seed with writable density
properties. Read the actual property unit. Assign the request density directly
when the property identifies kg/m³, and use unit conversion only when the
declared property unit requires it. Use the copied material's document-owned opaque
appearance where available. Otherwise create an opaque appearance in the
design and assign it to the body. Record that fallback as a body override
in the receipt and limit the comparison to resolved color and the requested
physical properties. If that distinction matters to the presentation claim,
prepare a same-source-type control and require it before qualification.
Abort the matching-material stage if required authoring or readback fails.
[Material copy](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Materials_addByCopy.htm)
· [Property units](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_FloatProperty_units.htm)
· [Opaque appearance](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Appearances_add.htm)

## Fresh-process bracket per candidate

Use four distinct task-owned Fusion process identities per exact candidate
digest. Record PID, creation time, launch ancestry and owner/session
identity, application build, start/end times, artifact and harness digests,
dialogs and errors. Require zero open documents at entry and exit. Close
every task document and retire only verified task-owned processes. The
archive-free role has no source-archive import stage. The independently
authored control is the native reference.

1. **Control before.** Author the independent same-request design through the
   public API. Inspect geometry, material and presentation as authored. Export
   locally, close, reopen exact control bytes, rebuild and measure again.
   Record its digest. Probe an independent height different from the
   candidate height so the healthy control exercises the positive rebuild
   path. Pin the healthy exact control archive for the after stage.
2. **Candidate.** Open exact generated bytes with no repair or empty
   viewport. Record before rebuild, rebuild and inspect. Move timeline before
   the extrusion, check zero solids and intact sketch, advance, rebuild and
   inspect again. Edit the height driver to the predeclared distinct value,
   rebuild and export. Restore its original expression, rebuild and export
   to a separate file. Save exact digests and recheck the original candidate
   hash. Exercise each independent width and depth driver in additional
   paired edit and restore observations when claiming that axis can rebuild.
3. **Reopen.** Import both exact candidate exports one at a time in this new
   process. Verify named graph, volume, center, bounds, area, material and
   presentation before and after rebuild. Strict-read each export afterward
   in a new offline SDK process and compare it with its expected authored
   state. Show the edited and restored driver values survived.
4. **Control after.** Reopen the exact independent control from stage 1,
   measure before and after rebuild, then exercise the separate height edit
   again. Compare to the before control and its numeric targets. An unhealthy
   control, wrong hash, or incomplete process ownership invalidates the batch.

For each measured state retain the exact three driver names, literal source
expressions and display units, both driving sketch dimension bindings,
dimension operands, the fixed corner distinct from sketch origin, the
construction plane, four oriented edges, profile membership, extrusion
extent reference and direction, named history and body ownership. Absolute
native object identifiers and auto-assigned model-parameter names may differ
by author. Compare the resolved roles and dependency references. For
positive-axis cubic geometry of width `w`, depth `d` and height `h`, require
one solid, six faces, twelve edges, eight vertices, volume `w*d*h`, center
`(w/2,d/2,h/2)`, area `2*(w*d + w*h + d*h)`, and origin-aligned bounds
`[0,w] × [0,d] × [0,h]`. Use the existing oracle tolerance of `1e-8`
absolute and relative in native centimetre-based units and record it.
[Existing geometry observations](../LocalOracle/EncoderRoundTrip/Measure.py)

## Matter and display evidence

Compare selected material label, density and physical mass against the
request and the independent control. Convert request density from kg/m³ to
kg/cm³ and require `mass = density * volume` in the same units. Keep the
raw asset identities and source-type values for all observed role bindings,
plus reported property IDs, values and unit declarations. Compare effective
body appearance and all six inherited face appearances by their geometric
roles. Require the exact requested RGBA channel tuple through the primary
color API, and record surface family, roughness, connected resources,
appearance-source type and other properties where observable. A fallback
body override may support the color check while leaving assignment semantics
open. Unspecified seed properties become evidence only after an actual
comparison shows they match.
[Material and camera observation](../SavedCuboidWriter/ObservePresentation.py)

Observe the loaded viewport before applying a fixed camera. Capture fixed
front and isometric outputs of matching controls and candidates with an
identical framing, visual style, lighting, background and resolution.
Calibrate silhouette and interior color tolerances on repeat same-state
controls before evaluating candidates. Measure saved embedded preview
members separately from the rendered viewport, with mode, roster, dimensions
and pixel digests. A missing preview or graphics companion on existing
research output needs exact load/regeneration evidence before claiming it
is valid to omit. The prior presentation plan has comparison and refusal
criteria for unavailable observations.
[Presentation and preview checks](../SavedCuboidWriter/PresentationOraclePlan.md)

## Current status

The first baseline attempt stopped during independent control setup. The
new control had no candidate open when Fusion rejected the schema unit as a
unit-converter token. The control reported zero documents on entry and exit.
The failed receipt SHA-256 is `45cfc4755c9f5a2ccc04a13ca0ab2c53a3c7044bb2c4fb744e50b4a30cd5a359`.
Recognizing `KilogramPerCubicMeter` as kg/m³ corrected the scale and the
independent control read back both density properties at 1,175 kg/m³.
[Material density units](../../../Documentation/Gotchas/Conversion/Fusion/Api/MaterialDensityUnitTokens.md)

The baseline then passed its four distinct Fusion 2706.1.17 process stages.
Each stage entered and exited with zero documents. The durations were
6.965, 35.500, 6.679 and 3.713 seconds for control, candidate, reopen and
control repeat. Candidate `ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be`
opened, rebuilt, rolled back before the extrusion and restored its feature.
Native changes independently moved height to 32.6 mm, width to 26.8 mm and
depth to 19.1 mm, with predicted volumes 23.053416, 14.147184 and 6.468597 cm³.
Restoring each respective driver returned 11.243844 cm³.

The independently reopened height edit was
`9b8f934ec40f60d6abf76379b35789b4a32a732148cef2acb1c9e7a96d499c4a`.
The restore was `d7429b483edba58091e723daac1005b5fff0e587f4f73007930cb6cc69deb756`.
Both native saves passed a fresh SDK strict read with persisted JSON native-state
equality. Each contains one saved snapshot, a graphics scene and two previews.
The baseline receipt index SHA-256 is `60281519b9600c7a773f813d9305744091d3ee019ebad0e14c9cf38723e50ffb`.

The separate JSON height-edit candidate
`8a28cf09b4e48108ca475d468b9e477314b92dfe1dedbf0715920ab0712682e3`
also passed four distinct Fusion 2706.1.17 stages with zero documents at
entry and exit. The durations were 4.054, 3.428, 4.174 and 3.141 seconds.
Its native height edit changed the measured volume from 17.466852 to
23.053416 cm³. Reopening the exact edit and restoring the original height
returned 17.466852 cm³. Batch SHA-256
`33da15703b2fb53491fbc6b3cbb4bb735f8d60e4e7d73cf9d4ed1acf422c7519`.

| Native save | Native SHA-256 | Persisted SDK JSON SHA-256 |
| --- | --- | --- |
| Height edited to 32.6 mm | `b2cc702656f7de7e95e6df78781bb9f245f4b6635e69eb45d0ccb3b9efb7182b` | `441c0e784244b47d992ece67385e91b83940fcce7abc10fb571d7644c59fefe3` |
| Height restored to 24.7 mm | `13fcc5e379c929298f37150bd18853cac44e9c44a0e0c3067f554307b824b7f1` | `e191519c94670ea1e47925f1bdd4ae480d18a8163d3f9fe608b7b43ed6fd019b` |

Both exact saves passed an offline SDK strict read and whole typed native
state equality after durable JSON. Both contain one snapshot, a graphics
scene and two previews. The first JSON write was blocked by the full system
drive. The retry wrote new copies on separate storage and verified equality.

The post-freeze holdout reached only the independent before-control startup.
The operator fenced the next stage when the system drive ran out of storage.
The control's bridge timed out and the task-owned Fusion process exited.
The exact held-out candidate has offline evidence and has yet to open in Fusion.

In both completed brackets, the independent control and candidate agreed on
label, density, physical mass and selected effective RGBA. The control obtained its color through a body
override. The candidate inherited a material-linked appearance. The broader
property probe reported `Ns::Types::IsUnitValueValid(unit)`, and viewport,
dialog, selection and archived preview comparisons remain open. The measured
geometry and material comparisons do not extend to those behaviors.
