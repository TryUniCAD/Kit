# FCStd to SOLIDWORKS corpus coverage

Status: **0 of 165 FCStd parts and 0 of five FCStd assemblies qualified**.
Kit's generative public writer accepts the scoped neutral line-loop and the
two qualified fixed-centre circle blind bosses. Its held-out native
SOLIDWORKS examples are separate from the FCStd benchmark. The earlier writer measured below re-emitted a recorded
vendor stream per family, so it was removed from production.
See the [native part writer](../../Documentation/Changes/Solidworks/Construction/SolidworksNativePartWriter.md).
See the [circle writer registration](../../Documentation/Changes/Solidworks/Construction/SolidworksCircleWriterRegistration.md).
See `Documentation/Changes/Solidworks/SolidworksRecordedPayloadRemoval.md`.

The figures below are the last audit of that removed writer. They record which source histories it
accepted and which oracle checks it passed. They are research evidence for a generative serializer,
not current capability.

## Generative 2026 research

Two [public SDK blank drawing cases](measurements/2026/SdkPublicBlankDrawingHeldout01.json)
matched their pre-registration locked native sources through rebuild, scale
edit, save and fresh reopen. The guarded builds use independently authored
neutral drawing inputs and generate all seven streams. These are drawing
layout acceptance cases outside the FCStd part and assembly benchmark.

The [internal SDK plain note](measurements/2026/SdkPlainDrawingNoteConstruction01.json)
reproduces two disclosed note containers and fourteen logical streams across
four guarded workers. Its first exact container passed the disclosed note text
and position lifecycle. Five further generated cases exercise the
[document display controls](measurements/2026/DrawingPlainNoteDisplayFlags01.json).
They retain the actual note data and ordered tree while the viewport still
omits the note. The [native edit diagnostic](measurements/2026/DrawingPlainNoteMemoryChanges01.json)
measures temporary redraw pixels followed by an identical blank image after rebuilding.
A separate [nine-process omission comparison](measurements/2026/DrawingNoteViewportCache01.json)
retains identical presentation when all three saved graphics streams are omitted
from the disclosed native drawing. Original source admission and held-out note acceptance remain
open. These drawing samples add zero generated FCStd conversions.

The independent research composer generates fresh native containers and streams
from neutral polygon, circle, radial-dimension and depth inputs without saved-stream inputs.
Its research results remain separate from public SDK and FCStd acceptance.

The [native single-solid body reader](measurements/2026/SdkNamedBodyRead01.json)
preserves the actual name and B-rep design-body link in four disclosed native
saves. All 22 process checks pass. These are reader inputs and add zero generated
FCStd conversions.

The [property-section drawing comparison](measurements/2026/DrawingBlankPropertySectionsNative01.json)
generates the native text-section and name-dictionary framing from neutral
sheet values. Two guarded builds agree with zero runtime input reads. The
corrected complete blank opens, rebuilds and accepts a scale edit, then
returns SaveAs error 1. Four reference lanes save and reopen in the
nine-process batch. This experiment adds zero production conversions.

The [appearance repair measurement](measurements/2026/FreshPartModelAppearance.json)
first opened the generated H3 part with its sketch and extrusion suppressed and
zero bodies. The
[configuration progress measurement](measurements/2026/FreshPartConfigurationProgress.json)
now opens and regenerates a fresh generated H3 part into one solid without
intervention, with zero errors or warnings between healthy original controls.
The locked input hashes remain unchanged. The subsequent
[three-case native batch](records/PolygonNativeMeasurements2026.md) passes
baseline geometry, live depth edits, save and fresh-process reopening for the
triangle, pentagon and heptagon, with healthy controls and zero errors or
warnings. This is the measured polygon subset only. No native assembly,
broader feature coverage or FCStd conversion is counted.

The later [canonical-flag measurements](measurements/2026/PolygonCanonical/README.md)
measure the three changed material-flag outputs directly, without transferring the
older files' acceptance. All three input hashes match the generated files from
CI artifact `14186359068` at `8d786b341ed291ee7e47fc1964ce7bc64014df04`.
Geometry, selected views, a depth edit, save and fresh reopening pass between
healthy controls. All 72 independent scalar comparisons pass, and all 90
standard-view arrays match the controls.
Full feature-name preservation fails: each reopened copy renames its material folder.
Initial-camera parity remains unestablished.
These are three measured polygon research outputs and zero completed FCStd conversions.

Two [generated free-circle sketches](measurements/2026/CircleSketchInspection01.json)
passed four native load/rebuild/save/fresh-reopen phases and 48 numeric/frame checks.
Two [free-center radial sketches](measurements/2026/RadialSketchInspection01.json)
and two [fixed-center radial sketches](measurements/2026/FixedCircleInspection01.json)
each passed six native phases and 104 numeric/frame checks, including driving radial edits.
The fixed-center inputs were fully constrained and retained the exact native center relation.
Two [generated blind circle bosses](measurements/2026/CircleBossInspection01.json)
then passed six native phases and 200 numeric checks, including one solid body,
volume, area, center of mass, radial/depth edits, saves and fresh reopens.
Two further [Right/Top principal-frame bosses](measurements/2026/CirclePrincipalInspection01.json)
passed six native phases and another 200 numeric checks, including independent radial/depth edits,
saves and fresh reopens. Their positive generation records passed all sixteen archive comparisons;
the same remote job separately failed its saved-reader gate and is not counted as green.
Every native batch had healthy original controls; all numeric comparisons matched to six significant figures.
These are bounded generated research rungs, not completed family acceptance or FCStd conversions.
Vendor-saved copies are derivatives and do not increase the generated-output count.
The six original Front-plane vendor-saved derivatives passed [54 archive comparisons and
108 numeric/frame checks](measurements/2026/SavedCircleReaderProcesses3d782d.json); these
reader inputs add zero generated-output cases. A [new inspection of the unchanged four bosses](measurements/2026/CircleInitialInspection01.json)
then passes all twelve phases with one body and active named sketch/boss features before any explicit rebuild,
plus all 400 rebuilt geometry/frame/mass/edit comparisons between healthy controls. This adds no generated cases.
Initial viewport/camera and complete presentation remain unestablished for the circle bosses.

Two [disjoint circle-set sketches](measurements/2026/CircleSetInspection01.json)
passed four controlled native phases and all 72 numeric/frame checks, with two/four requested circles,
an active sketch, zero requested bodies, rebuild, save and fresh reopen. Their [remote generation](measurements/2026/CircleSetProcessesF00d6e.json)
passed sixteen byte comparisons; equal-length names, the same plane and an unchanged two-circle prefix
isolate the resolved-stream growth from 6,795 to 7,607 bytes while Config-0 stays at 21,138.
These two generated research inputs still add zero completed FCStd conversions and no held-out family acceptance.

Two [ordinary signed open-arc sketches](measurements/2026/OpenArcInspection01.json)
passed four controlled native phases and all 64 numeric/frame checks, including both endpoints,
positive/negative native rotation, rebuild, save and fresh reopen. Their
[remote generation](measurements/2026/OpenArcProcesses61622d.json) passed sixteen complete byte comparisons
with strict process/read guards. Controls were healthy and inputs immutable. These are two bounded free-sketch
research outputs, with zero requested bodies and zero new completed FCStd conversions or held-out family acceptance.

Two [mixed line/arc capsule sketches](measurements/2026/MixedCurveInspection01.json)
then passed four phases, all 124 numeric/frame checks and actual shared native identities at all four joins.
Their [process receipt](measurements/2026/MixedCurveProcesses26c200.json) retains sixteen complete comparisons,
strict read guards and nineteen unchanged prior neutral outputs across the shared composer change.
These free sketches add no completed FCStd conversion or held-out acceptance; body/depth behavior needs its own measurement.

Two [capsule blind bosses](measurements/2026/CapsuleBossInspection01.json) subsequently passed six phases,
including an initial body before explicit rebuild, analytic mass targets, depth edits, saves and edited fresh reopens.
All 304 original numeric checks pass with maximum relative error `5.680912614542858e-16`; the receipt retains two
one-unit rounding ties that differ under six-digit text formatting. Both controls passed and inputs remained immutable.
Their [generation receipt](measurements/2026/CapsuleBossProcesses7915de.json) retains sixteen complete archive comparisons
and strict process/read guards. No radius/length driving dimension, tangent constraint, full presentation, held-out acceptance
or completed FCStd conversion is counted.

The [complete circle/arc source lock](v2026/heldout/CurveSourceLock.json)
records 30 vendor-authored source cases, 66 fresh phases and 797 passing checks.
Those source files are not generated Kit outputs and add zero writer-coverage cases.
The six held-out native payloads remain sealed during derivation and implementation.

The separate [end-condition source lock](measurements/2026/EndConditionSourceLock02.json) adds sixteen vendor-authored
source cases, 38 fresh phases and 437 passing numeric checks between healthy controls. It locks twelve discovery and
four held-out inputs for forward/reversed blind, mid-plane and two-direction bosses. All eighteen original native hashes
and 32 sibling hashes were verified. Fourteen discovery/control inputs were [privacy-prepared](measurements/2026/EndConditionPreparation02.json)
for independent reader comparison in remote CI, which remains pending. All ten held-out native payloads across both
source families remain sealed; this adds zero generated outputs, held-out writer results or FCStd conversions.

Three [new generated end-condition bosses](measurements/2026/EndBossInspection01.json) now pass reversed blind, mid-plane and
two-direction native body/edit checks. An unchanged prior circle baseline is included separately and adds zero new outputs.
All twelve candidate phases and 432 original numeric checks pass between healthy controls, including initial bodies,
independent radial/first-depth/second-depth edits, save and edited fresh reopen. Maximum nonzero relative error is
`6.917216933756428e-16`; zero targets are exact and two decimal rounding-boundary disagreements remain explicit.
Their [generation receipt](measurements/2026/EndBossProcesses4b51.json) records 24 complete archive comparisons and
23 byte-identical prior tagged neutral outputs. No full presentation, held-out family result or completed FCStd conversion
is counted, and all ten held-out native payloads remain sealed.

The later [ordinary-folder held-out rung](measurements/2026/TreeParityInspection01.json)
passes two new generated circle bosses against their independent native sources:
twelve paired phases, 840 numeric checks, 440 exact pose comparisons and 22
ordered-tree comparisons. Every tree has the same 25 named/typed/parented nodes;
all forty scenes have one visible body. Radius/depth edits, native saves and
edited fresh reopening pass between healthy controls, with fourteen distinct
process creation identities, unchanged input hashes, idle postflight and unchanged
licensing process IDs. These are bounded English tree/pose research outputs,
not completed FCStd conversions or complete format acceptance. The public
adapter remains read-only and the requested production corpus count remains zero.

The [six vendor-saved derivatives](measurements/2026/TreeSavedReadbackProcessesEfe1.json)
also pass 54 archive comparisons, 108 semantic values and 102 exact pose
values. The readback confirms the actual markup class and model-to-sketch
transform in the saved files. These derivatives add no writer outputs. The
[field direction record](records/ProfileTransformDirection2026.md) identifies
an opposite-direction seed in the frozen research emitter. The current
research emitter computes the inverse placement. Two new Top and Right
sources were [locked](v2026/heldout/FrameSourceLock.json) before the correction.
The [remote predictions](measurements/2026/FrameHeldoutProcesses34a.json)
pass 16 full archive comparisons and 26 transformed values. The
[paired native result](measurements/2026/FrameParityInspection01.json)
passes 12 phases, 840 numeric checks, 572 exact profile transform values and
22 ordered feature trees. All 50 paired mass-property values agree to six
significant figures. These two generated circle bosses add no completed
FCStd conversions or native assemblies. The public adapter is read-only.

The [synchronized assembly source lock](v2026/heldout/AssemblySyncSourceLock.json)
now qualifies five native empty, single and repeated-component inputs,
including two held-out parents with intact child hashes. The independent
[completion record](measurements/2026/AssemblySyncSourceCompletion03.json)
passes ten phases, 900 numeric comparisons and zero reopen warnings between
healthy controls. These five files are oracle-authored sources and are
excluded from generated coverage.

The [concentric source lock and linked archive trial](measurements/2026/ConcentricMateSourceArchive01.json)
passes twenty-five native processes for three disclosed and two
guest-private source cases. Both actual persistent cylindrical faces
resolve to their owning inherited occurrences. The six disclosed
states re-emit eighteen complete linked streams and preserve their
measured alignment and rotation-lock choices. The source locks add
zero generated conversions.

Two [generated empty research assemblies](measurements/2026/EmptyAssemblyNative01.json)
now match the native discovery control through open, rebuild, save and fresh
reopen, with all ten candidate observations and four controls passing.
The generated research count is two empty assemblies. Neither has components
or mates, neither is a held-out conversion, and neither adds an accepted
FCStd assembly to the production count of 0/5.

A third [generated empty assembly with a self file record](measurements/2026/AssemblySelfReferenceNative01.json)
also passed open, rebuild, save, fresh reopen and the native tree comparison.
The [first generated populated assembly](measurements/2026/GeneratedSingleOccurrenceNative01.json)
then opened, resolved its generated child, rebuilt and saved with zero errors and warnings.
Both generated and freshly reopened phases rebuilt with the same 23-node feature tree and one-body geometry,
passing all 42 numeric checks. The saved derivative returned warning 32 on fresh open between healthy controls.
In a [paired save comparison](measurements/2026/GeneratedOccurrenceSaveComparison02.json), the same
generated inputs reopened without warning or rebuild requirements after saving the rebuilt child and
parent in order. The parent-only lane reproduced warning 32. Both lanes matched the same 23-node tree
and one-body geometry, with 84 numeric checks and four healthy controls. This adds one generated
single-occurrence research case. The production counts remain 0/165 parts and 0/5 assemblies.

The [generated repeated-occurrence measurement](measurements/2026/GeneratedRepeatedOccurrencesNative03.json)
adds an assembly with three resolved placements of the same generated child. It passed clean open,
rebuild, synchronized save and fresh reopen with 106 numeric checks and two healthy controls.
The two observations preserve a 25-node tree and three placed bodies. The synchronized assembly
held-outs remain sealed, and no production conversions are counted.

The [generated ordinary revolve measurement](measurements/2026/GeneratedRevolveSketchLog02.json)
adds full-turn, forward partial and reverse partial parts. Each opened and rebuilt with zero errors
and warnings, produced one solid with the expected mass properties, and passed a driving angle edit.
All 75 numeric checks and both controls passed. The generated files use the sketch's actual log state
for axis-reference creation time. The [edited-save and fresh-reopen result](measurements/2026/GeneratedRevolveEditedReopen04.json)
adds 111 numeric checks across eight distinct SOLIDWORKS processes. With the native empty-material caption,
all three candidates preserved their edited angle, signed geometry and exact 20-node tree on fresh reopen.
Both controls passed. This cohort used disclosed designs and the production totals are unchanged.

The [paired revolve comparison](measurements/2026/GeneratedRevolveCanonicalComparison05.json)
uses canonical English folder roles in three new generated files. Every candidate exposed
one body on open. All three matched their independently authored 19-node trees, driving edit,
model-space geometry and sketch frame, including clean fresh reopen of each edited derivative.
Both controls passed. The [prediction freeze](v2026/heldout/OrdinaryRevolvePredictionFreeze01.json)
pins the generator, fixtures, oracle and both comparison tools before held-out disclosure.

Both [ordinary boss revolve held-outs](measurements/2026/GeneratedRevolveHeldout06.json)
passed locked native comparisons for their tree, signed geometry, sketch frame and driving-angle
edits. The two saved derivatives reopened cleanly between healthy controls, across six distinct
processes. The [prediction record](v2026/heldout/OrdinaryRevolveHeldoutPredictions01.json)
retains the original freeze and documents the model-space verification correction before revealing
the reference results. This qualifies the research profile for a single ordinary boss on a
principal plane. The public writer and production corpus totals are unchanged.

The [drawing Definition receipt](measurements/2026/DrawingDefinitionCheck01.json)
records six byte-exact archive comparisons and 78 native semantic observations for three disclosed
SOLIDWORKS 2026 drawings from the [drawing source lock](v2026/heldout/DrawingSourceLock01.json).
The [SDK drawing layout receipt](measurements/2026/DrawingSdkLayoutCheck01.json) verifies a
partial reader in the public adapter for those three native drawings. It supports the sheet and
single external part view layout. The [raw Definition proof](measurements/2026/DrawingRawGrammar01.json)
re-emits both original streams byte for byte. The [empty appearance-manager receipt](measurements/2026/DrawingEmptyAppearanceReader01.json)
advances both original reads to the root guard. The [typed detailing index proof](measurements/2026/DrawingDetailingIndexRead01.json)
keeps the actual edge-reference graph and marks its portable edge projection open. Both originals
retain their [typed view rendering state](measurements/2026/DrawingViewRenderingRead01.json)
and reach the sheet annotation check. Strict drawing reads and production writing await further qualification.
The [drawing concept prefix check](measurements/2026/DrawingConceptPrefixCheck01.json)
round-trips the ordered sheet and complete view records before the resolved model tail. The
research reader extracts model orientation, scale and the view transform and compares them
with the native observations in both view-bearing cases. The [SDK view receipt](measurements/2026/DrawingSdkViewRead01.json)
verifies the same Definition properties and reference ownership through the public opt-in adapter.

The [scaled drawing inspection](measurements/2026/DrawingScaledViewSdkRead01.json)
covers disclosed Front, Top, Right and Isometric views at four non-unit
scales. It passes complete Definition and Header2 byte identity and 36
geometric probes through the public opt-in SDK reader. All four layouts
survive neutral JSON serialization. Native source authoring and fresh
reopen pass across ten processes.

The [scaled view construction](measurements/2026/DrawingScaledViewBuild01.json)
produces four distinct drawing and part pairs from independently supplied
neutral requests. Two builds per case are identical and record zero
runtime input-file access attempts. The prior unit-scale Front pair
retains its original file hashes. In the [native generated comparison](measurements/2026/DrawingScaledViewNative01.json),
the four new pairs and both pristine brackets pass twelve processes and
1,194 numeric checks. All four generated drawings save and freshly
reopen with the moved view, scale, orientation, child link, configuration,
measured geometry and exact sixteen-row tree. The SDK reads the four
saved layouts. Held-out drawing qualification remains open.

The [combined blank drawing diagnostic](measurements/2026/DrawingCacheCombinedOmission01.json)
shows that SOLIDWORKS regenerates four omitted display and preview streams
after editing and saving the disclosed empty sheet. Both controls, the
repacked control and the four-stream omission passed clean reopen over
eight processes. This comparison measures the native reduction controls.

The [first generated blank drawing](measurements/2026/GeneratedBlankDrawingNative01.json)
opened and rebuilt cleanly. It retained the ten expected feature rows and
accepted a sheet scale edit. Native SaveAs returned error 1 and produced an
empty target. The reduced native control with the same seven stream roles
saved and reopened cleanly.

The [matched-path cosmetic-thread comparison](measurements/2026/GeneratedBlankDrawingThreadFlagNative02.json)
retained identical native save failures for both generated inputs. All
three controls passed over eight fresh processes.
The [save-mode comparison](measurements/2026/GeneratedBlankDrawingSaveModes03.json)
reproduced error 1 before a scale edit and in a writable in-place save.
The reduced native control saved and reopened in both modes.
The [target-state repeat](measurements/2026/DrawingBlankSaveEventStateNative01.json)
distinguished the zero-byte generated target from the absent target after a
calibrated event 7 veto. Both share the same error and event sequence.
All three matched controls passed.
The [matched software trace](measurements/2026/DrawingBlankSaveAggregateSoftwareMatchedNative01.json)
measures a zero event aggregate in the reduced-native and generated blank
drawings. The generated drawing still produces only event 7 and a zero-byte
target. Both pristine checks and the traced reduced control save and reopen
cleanly. The failing downstream save action remains open.
The [document return trace](measurements/2026/DrawingBlankSaveDocumentReturnNative01.json)
observes the same document save call return 1 for the reduced-native
drawing and 0 for the generated drawing. The internal storage and
serialization branch remains under measurement.
The [storage gate trace](measurements/2026/DrawingBlankSaveStorageGateNative01.json)
observes a valid root in both lanes before the generated failure.
Native drawing writing remains unqualified.
The [property-prefix correction](measurements/2026/DrawingBlankPropertyPrefixNative01.json)
changes only the retained property's XML lexical binding. The generated
blank sheet passes native scale edit from 2:3 to 3:2, SaveAs and fresh reopen
with its original ten feature rows. All four control lanes pass in ten
native processes. The SDK reads the saved scale and dimensions from the
generated derivative's native layout. This evidence covers a disclosed
empty sheet. Held-out drawing and production writer qualification remain open.

The [typed UI omission comparison](measurements/2026/DrawingBlankUiOmission01.json)
passed fourteen native phases. The reduced native document saved with its
viewport, line tables, environment and BOM state omitted together.

The [disclosed front-view detailing map trial](measurements/2026/DrawingFrontDetailingMapOmission01.json)
preserved the view edit, linked part and feature tree in sixteen passing
native phases. The two omission derivatives kept the map empty through
save and fresh reopen. Generated populated drawing acceptance remains open.

The [generated front drawing and part trial](measurements/2026/GeneratedFrontDrawingNative01.json)
passed clean native open, rebuild and the measured view movement while
retaining the exact sixteen-row drawing tree and expected child geometry.
Native SaveAs returned error 1 and left an empty target. Both pristine
controls and the reduced native drawing with the same seven stream roles
passed through save and fresh reopen across the seven-process batch.
The reduced derivative also regenerated the omitted detailing map.

The [corrected linked drawing trial](measurements/2026/DrawingFrontPropertyPrefixNative01.json)
passes actual view movement, native save and fresh reopen with its generated
child. All eight phases pass, including the pristine brackets and
same-role reduced control. The sixteen-row drawing tree, child link,
configuration and geometry survive save. The SDK reads the edited view
position and model reference in the native derivative. This comparison
covers one disclosed unit-scale front view on an unformatted sheet.

The [original held-out front-view trial](measurements/2026/DrawingOriginalHeldoutNative01.json)
qualifies two native drawing and ordinary rectangle pairs for the measured
layout and linked edit profile. The two generated pairs match their original
sources across 1,900 registered comparisons, including ordered feature
trees, edited view state, linked child geometry, save and fresh reopen.
Both controls pass across twelve distinct native processes. This research
measurement adds no qualified production conversion.

The [original SDK drawing comparison](records/SdkOriginalDrawingNativeComparison2026.md)
matches geometry for both source pairs through native view movement, save
and fresh reopen across twelve processes and 1,704 comparisons. Both cases
retain 13 differing drawing feature names and a linked child with a distinct
notes folder class and feature row count. These two pairs do not pass
source-semantic acceptance.

The [raw Definition grammar proof](records/DrawingRawGrammarBoundary2026.md)
reads and writes every byte of the two original Definition streams through the
typed graph. Both maps and object identities survive. That proof records an
initial UI state rejection for the present PW material owner. The later
[typed detailing verification](records/DrawingDetailingIndexRead2026.md)
reaches the view rendering check. The [rendering-state verification](records/DrawingViewRendering2026.md)
exposes an annotation guard triggered by a view-owned profile display. The
[typed profile display check](measurements/2026/DrawingProfileDisplayRead01.json)
then completes both internal named Definition round trips with identical bytes,
map slots and actual aliases. Portable display, colour and edge links and full
drawing conversion remain open.

The [signed linked text-depth trial](measurements/2026/DrawingSpatialTextNative01.json)
passes two disclosed native edit, view move, save and reopen lifecycles
in ten processes with both controls healthy. The corrected archive
observer passes ten exact joins across Definition and the three child
streams. The observed positive and negative stored depths survive the
edits. Full drawing source and public writer acceptance stay open.

The [fresh ANSI detail graph](measurements/2026/DrawingAnsiStyleConstruction01.json)
passes 26 guarded codec workers and ten typed comparisons. It preserves
the known constructor state through the native standard default
operation. The disclosed original graphs retain separate source fonts,
nested units and other unqualified fields. Native acceptance of the
fresh ANSI operation remains open.

The [paired ISO and ANSI native trial](measurements/2026/DrawingAnsiPairNative01.json)
passes both controls, 3,700 numeric comparisons and the native
edit/save/reopen lifecycles of both shapes under both standards. All
twenty snapshots preserve the actual links and re-emit the complete
linked archive streams. The full style check fails on 184 ISO and 185
ANSI first-save differences. Original-source and held-out qualification
remain open.

The [document-style initialization experiment](measurements/2026/DrawingDetailInitialization01.json)
derives the dimension formats, Swift settings and positive exclusion
lists from neutral inputs and exact native rules. All 32 host workers
pass. Each of the four comparisons keeps every resolved field and alias
while advancing the linked map by eight actual dual-unit objects.
The new native persistence and full style checks remain open.

The [matched blank framing trial](measurements/2026/DrawingBlankFramingNative01.json)
passed both native save modes under the original and Kit containers.
The paired controls retain the same seven streams and compressed bytes.
The twelve-process trial used no generated or held-out drawing inputs.

The [rectangle dimension receipt](measurements/2026/GeneratedRectangleDimensionsNative01.json)
verifies two generated Front Plane rectangles with independent driving width and height edits.
Both edited dimensions survived clean save and fresh reopen. The rebuilt geometry matched the
analytical results and independently authored native reference parts. Both controls passed across
22 processes. The generated and reference trees have 20 and 19 nodes respectively.
The production coverage counts are unchanged.

The [original corner held-out](measurements/2026/RectangleCornerHeldoutNative01.json)
and [original centered held-out](measurements/2026/RectangleCenterHeldoutNative01.json)
retain all 25 source feature rows and full native constraints through
independent width and height edits, clean saves and fresh reopen. Both
first candidates pass. The centered model keeps both construction diagonals
in its saved files. These are research cases from independently authored
neutral specifications.

The [SDK origin-anchored experiment](records/SdkRectangleCornerNative2026.md)
passes all three independent width, height and depth edits from the same
generated part. The corner remains at the model origin in every native state.
Both controls and all eight processes pass. The resulting synthetic shape
establishes the editable geometry needed for the scoped FreeCAD primitive.

The [disclosed FreeCAD origin box](records/SdkFreecadOriginBox2026.md) enters
the shared constructors through the actual strictly decoded neutral source.
The [shared SDK proof](measurements/2026/SdkFreecadBoxSharedBuild01.json)
reproduces both native-tested files in six guarded builds, including
two with the source cache and stored payloads removed. The named box
retains its actual body and three editable driver names through 162
native checks. Original benchmark membership remains unverified, so
this adds zero corpus passes. The [strict cache-free readback](records/SdkNoCachePrismRead2026.md)
recovers one solid with eight vertices, twelve edges and six faces, and
retains all three drivers, seven relations and thirteen text properties.

The [custom mass-unit lifecycle](measurements/2026/SdkCustomMassUnitsNative01.json)
passes four generated parts through native depth edit, save and fresh
reopen. Both mass choices remain independent of the correct effective
body mass and geometry. Eight normal SDK reads retain the modeled
solid and driving depth. This setting qualification adds zero original
FCStd corpus passes.

The [public document unit read](measurements/2026/PublicDocumentUnitsRead01.json)
preserves the scoped custom mass choice and native precision in fourteen
disclosed states. Three preset states and six unqualified custom records
omit the optional metadata while their strict model reads pass.

The [release-specific FreeCAD box proof](measurements/2026/SdkFreecadBoxReleaseConstruction01.json)
audits twelve schema-four inputs. Three disclosed origin-box forms
build with exact driver and text recovery, and nine attached or
multi-feature variants reject. Four targeted mutations also reject.
The two newer-release [native lifecycles](measurements/2026/SdkFreecadBoxReleaseNative01.json)
pass all driving edits, clean saves and fresh reopens with the actual
kilogram setting, body name and literal text. Four strict readbacks
pass forty complete stream comparisons. Historical-original membership
remains unverified.

The two [original SDK circle parts](records/SdkOriginalCircleNative2026.md)
pass native source parity for translated Front-plane diameter and reversed
Top-plane radius. All 14 controlled phases and 400 recorded numerical checks
pass, including edits to the radial size and depth and a clean fresh reopen.
All sixteen normal SDK reads preserve both driving owners. These sources
are native SOLIDWORKS and add zero FCStd conversions.

The [normal part text reader](records/PartTextPropertyRead2026.md) recovers
the current compatible summary, file and configuration text with the actual
configuration owner on five files. The advanced property manager case keeps
its model read and reports its unsupported property scope. The six CMgr
streams re-emit exactly.
Complete source property and semantic mapping remains open.

The [dimensioned assembly trials](measurements/2026/GeneratedDimensionedAssembliesNative04.json)
verified independent width, height and depth edits in generated single- and repeated-occurrence
bundles. All six trials matched their independent native geometry and exact recursive part and
assembly trees through clean native open, rebuild, synchronized save and fresh reopen.
Both controls passed in a 26-process batch. The subsequent
[held-out comparison](measurements/2026/GeneratedDimensionedAssembliesHeldout05.json)
passed all 210 gates across another six width, height and depth trials in three- and
four-occurrence assemblies. Their parent and child files were generated before
the native comparison archives and outcomes were opened. The observer matched
both feature trees, configurations, component transforms, named dimensions and
mass properties through rebuild, synchronized save and fresh reopen. Both
controls passed across 26 distinct process births. This evidence qualifies the
research profile with one repeated rectangular child and no mates. Production
conversion coverage remains zero.

The [disclosed planar-mate readback](measurements/2026/AssemblyPlanarMateArchive01.json)
reconstructed 51 streams across three parent and child pairs, including three
populated mate lists. A subsequent [chain proof](records/PlanarMateReferenceChains2026.md)
qualified every executed serializer in the three lists. The
[generated endpoints](measurements/2026/GeneratedPlanarMateEndpoint01.json)
retained their actual parent, occurrence and child datum identities through
the typed archive, with placement-dependent lengths.

The [complete coincident assembly construction](records/AssemblyCoincidentConstruction2026.md)
emits the full mate list together with its fixed anchor, Config-0
reference counter and paired header logs. Both authored assemblies
round-trip the required archive graph. The [first controlled native trial](measurements/2026/GeneratedCoincidentMateNative01.json)
opens one generated pair with coplanar placements, verifies the exact datum
references and fixed anchor, then edits a driving depth and matches geometry
after synchronized save and fresh reopen. Both controls passed over four
processes. The [displaced pair](measurements/2026/GeneratedCoincidentMateActiveSolve01.json)
closes a 4.73 mm plane offset during open and preserves the solved placement
through rebuild, with three clean processes. Persistence from the displaced
start, held-out mate acceptance and production qualification remain open.
The [typed readback](measurements/2026/PlanarMateProjection01.json) matches the
two ordered plane IDs and explicit alignment across six generated and native
research inputs. The public assembly read still depends on the saved
selection strings for these mates.
The [SDK planar mate projection](records/PlanarMateSdkProjection2026.md)
implements the typed join shared by the research command and its fresh
generated process regression. The public route awaits production loaders
for the linked assembly and part archive maps.
The [parallel mate construction](measurements/2026/GeneratedParallelMateBundle01.json)
round-trips six streams in a distinct generated parent and child with zero
runtime input reads. The [native parallel trial](measurements/2026/GeneratedParallelMateNative01.json)
passes open and rebuild with two solid bodies and exact Front Plane
references separated by 22.61 mm. Both controls pass. Editing, save
and held-out qualification remain open.
The [driving distance mate construction](measurements/2026/GeneratedDistanceMateBundle01.json)
adds a separate guarded generated pair with six exact stream round trips
and zero runtime file reads. Its authored distance differs from its start
separation. The [typed projection](measurements/2026/PlanarMateProjection02.json)
reads the actual parameter from the generated graph. Native qualification
remains open.

The [exact-path distance replay](records/GeneratedDistanceMateNativeOpen2026.md)
resolves both children with clean native open and rebuild. The moving
Right Plane changes from a 43.875 mm gap to 71.375 mm, with both controls
passing. The full trial retains its failed verdict from an invalid expectation
of named sketch parameters. A [separate regenerated disclosed trial](records/GeneratedDistanceMateEdit2026.md)
edits the driving length to 88.125 mm, saves both files and verifies the
edited plane gap and geometry after fresh reopen. Typed readback resolves
the same reference identities and edited length. Held-out qualification
remains open.

The [shared SDK header graph](records/SharedSdkHeaderGraph2026.md) re-emits
31 standalone streams exactly across 17 disclosed files. The research
generators use the same codec for both header streams and reproduce four
earlier assembly bundles. The production corpus count is unchanged.
The [configuration handoff](records/ConfigHeaderHandoff2026.md) retains
those exact SDK header nodes across twelve linked archive reads and
stores, including the generated planar mate process regression.

The [disclosed nested audit](records/DisclosedNestedAssemblyArchiveAudit2026.md)
checks 42 streams in seven saved definitions and binds both healthy native
reopens. Direct directories, expanded occurrence counts, recursive stamps
and child-local bounds follow distinct measured owners. The
[pre-writer source lock](v2026/heldout/NestedAssemblySourceLock01.json)
qualifies both sealed author/reopen source sets in eight fresh processes.
Generated nested conversion coverage requires its own measured
acceptance through the public adapter.
The [recursive composer](records/GeneratedNestedAssembly2026.md) now
generates one part, one nested module and the root from the neutral
definition graph. Its 28 stream comparisons and SDK history read
pass. The four-definition repeated case also generates
deterministically. The [first controlled native nested trial](records/GeneratedNestedAssemblyNative2026.md)
passes open, rebuild, a live leaf-depth edit, synchronized saves and
fresh reopen across four distinct processes with healthy brackets.
The [typed saved-state comparison](records/GeneratedNestedAssemblySavedState2026.md)
passes 36 stream round trips and preserves the actual edited depth,
child stamps and local bounds. The [repeated native trial](records/GeneratedRepeatedNestedAssembly2026.md)
also passes across four controlled processes with seven expanded
paths and five solids. Editing the shared leaf changes all four of
its placements, and all four files save and reopen successfully.
Its typed audit passes 48 stream comparisons. The later
[blind evaluation](records/SealedNestedAssemblyEvaluation2026.md)
passes both pre-writer locked ordinary rigid nested assembly cases
across eight controlled native processes. It checks live depth edits,
rebuild, synchronized save, geometry and fresh reopen. The family
qualification adds zero completed FCStd conversions to the production audit.

The [explicit SDK planar group constructor](records/SdkPlanarGroupConstruction2026.md)
generates six disclosed groups of two, three and five direct occurrences of one
dimensioned part. Its 1,740 exact typed stream comparisons and eight atomic
rejections pass. Existing flat and recursive bundles retain exact bytes.
The [disclosed native group](records/SdkExplicitPlanarGroupNative2026.md)
passes 440 numerical checks across four processes through a live driving edit,
synchronized save and fresh reopen. The public reader retains all twelve
endpoint links and 26 scoped archive streams serialize byte-for-byte.

Both [original planar mate groups](records/SdkOriginalPlanarMateNative2026.md)
qualify this internal SDK profile. A20 has two direct occurrences with
coincident and distance mates. A21 has three with parallel and distance.
All ten native phases and 992 numerical checks pass, including each
generated distance edit, synchronized save and fresh reopen. The 26 scoped
native-saved stream comparisons pass. These internal cases add zero
qualified FCStd conversions.

The [portable registry assembly trial](records/SdkPortableAssemblyRegistryNative2026.md)
generates a three-occurrence parent and a shared dimensioned child through an
explicit writer registry. Four native processes pass 440 comparisons and
retain all six endpoints and three child drivers through a driving edit,
synchronized save and fresh reopen. The 26 scoped archive streams round-trip
exactly. This disclosed trial adds zero qualified FCStd conversions.

The [normal assembly writer](records/SdkAssemblyPublicRegistration2026.md)
reproduces both exact files from that registry trial and supports two or
three direct occurrences of one dimensioned rectangular child with ordinary
principal-plane mates. Its process checks cover preserved part output,
native Windows path selection, controlled publication failure and a
concurrently created companion. Original FCStd qualification remains open.

The [generated perpendicular mate trial](records/SdkPerpendicularMateNative2026.md)
passes native open, rebuild, pose and child depth edits, synchronized save
and fresh reopen with healthy controls. Its saved links and drivers pass
the normal SDK reader. This is a disclosed SOLIDWORKS self-lifecycle.

The [paired perpendicular assessment](measurements/2026/SdkPerpendicularHeldoutNative01.json)
passes both pre-writer locked SOLIDWORKS assemblies and their child parts.
All 484 native numeric checks, twelve source-to-generated comparisons and six
normal SDK source and saved-file audits pass. Four controls bracket the runs.
Both candidates come from the frozen neutral-only internal writer. These
SOLIDWORKS cases add zero FCStd corpus conversions.

The [public perpendicular registry evaluation](measurements/2026/SdkPerpendicularRegistryHeldout01.json)
runs those two source pairs against normal registry output. Both pass 484 checks
in total, twelve paired native comparisons and six strict SDK readbacks.
The qualified public writer covers this perpendicular profile.
The FCStd qualification counts stay at 0/165 parts and 0/5 assemblies.

The local FCStd inventory found 171 candidate paths across the retained FreeCAD,
public acceptance and CADMPEG source collections. These span 162 distinct SHA-256
identities with successful Document.xml discovery. The inventory includes 56
documents with pads, 38 with pockets, 25 with chamfers, 23 with holes and 20 with
revolutions. The original benchmark membership remains unverified. The private
inventory digest is `db7280b68f5bd30d5d3a3f8e3fe92b1ed335e7cd76786ae5cfbddb0064efa52c`.

The [strict neutral read census](measurements/2026/NeutralCorpusRead01.json)
reads the 162 validated FCStd byte inputs in the SDK with B-rep and
tessellation disabled. It finds two documents with assembly graphs,
132 with native feature definitions, 69 with typed extrusion definitions,
and 27 with typed chamfer definitions. These counts overlap within
documents. An independent path-input pass matches the counts and resolves
one external document link that the byte-input pass reports as unresolved.
Benchmark membership, semantic equivalence and SOLIDWORKS output are
separate checks. This census writes zero native files.
[Input mode behavior](../../Documentation/Gotchas/Conversion/Freecad/ByteInputsLackExternalReferenceOrigin.md)

The [blind-pocket discovery](measurements/2026/GeneratedBlindPocketNative02.json)
passed native open and rebuild for the generated all-bodies cut with one
solid, its driving depth and radius, and analytic geometry at six significant
figures. Its empty feature-scope sibling reported warning 32 and cut error 71.
Both controls passed across four processes. The subsequent
[native edit comparison](measurements/2026/GeneratedBlindPocketEdited04.json)
verified an 8.31 mm driving depth after fresh reopen with the canonical
material caption, all 28 tree rows and correct geometry. Independent
held-out qualification remains open.

The [complete SDK polygon held-outs](measurements/2026/SdkOriginalPolygonNative01.json)
pass for the original three-line, five-line and seven-line SOLIDWORKS
sources. Each generated part matches the native source tree and measured
geometry, retains an editable blind depth and opens cleanly after the
native edit and save. Eleven fresh processes and 546 checks pass with
healthy controls. These three cases qualify the scoped SDK construction.
The FCStd production count remains 0 of 165 parts and 0 of 5 assemblies.

## Last audit of the removed writer

The historical discovery in `tools/audit/FcstdDiscovery.py` at revision
`48ff095c9` counts resolved filesystem paths under the supplied recursive
roots. It defaults to the repository root in `FcstdArgs.py`. The Git tree
at that revision and both current checkouts contain zero FCStd paths.
The historical file roster remains unavailable. The later 162-count
inventory groups its available input paths by content hash. Reconcile
the original roster before using those two counts as a coverage comparison.
[Audit inventory counting](../../Documentation/Gotchas/Conversion/Freecad/AuditCountsResolvedPaths.md)

The audit tool, `tools/audit/AuditFcstdSolidworks.py`, was deleted with the writer. Its 2026-08-11
recursive result was:

| measurement              | count |
| ------------------------ | ----: |
| FCStd files              |   165 |
| parser or writer errors  |     0 |
| vendor-loadable contract |    44 |
| application-usable       |    44 |
| near-lossless            |    44 |
| vendor-only              |     0 |
| unsupported              |   121 |

121 sources were unsupported. Each accepted part went through the public `write_document` path,
and the resulting compound file was read back with `SldprtArchive`. The increase from 40 to 44 was
the exact six-line polyline pad, full stepped-pin revolution,
90-degree stepped-pin revolution, and rectangular boss/two-cut chain ending in a circle. This was a
production-path structural proof, not a claim that all 44 files were individually opened
in SOLIDWORKS. Vendor-application oracle measurements remain separately recorded in
`archive/Multistream.md`.

## Families the removed writer accepted

Each accepted source history was built from one recorded typed program, with editable sketches,
dimensions, feature ordering, and body-producing operations:

- rectangular and circular pad, including blind depth, reverse direction, mid-plane, and principal
  sketch-plane variants where the recovered grammar supports them;
- exact standalone `Part::Box` solids lowered to an origin-based rectangle with independently
  editable length and width dimensions plus an editable blind-boss height;
- exact standalone origin-aligned `Part::Cylinder` solids lowered to a diameter-driven circle with
  an independently editable blind-boss height;
- blind and through-all pockets, including two- and three-pocket chains;
- the exact three-stage rectangular boss, rectangular pocket, and circular pocket chain;
- pad followed by a second pad;
- full rectangular revolution, exact full and 90-degree stepped-pin revolutions, and pad followed
  by a groove;
- the exact connected six-line Front-plane blind pad;
- pad followed by fillet, chamfer, or shell;
- pad followed by linear pattern; and
- pad followed by circular pattern, including occurrence count, total angle, and reverse direction.

Every byte of the load-critical reference streams had a typed owner for these families:

| stream family                      | reference bytes | opaque bytes |
| ---------------------------------- | --------------: | -----------: |
| `Contents/Definition`              |           3,618 |            0 |
| `Contents/CMgr`                    |           1,957 |            0 |
| `Contents/Config-0`                |   25,158–25,214 |            0 |
| assembly core field program        |          38,198 |            0 |
| family-specific `ResolvedFeatures` |   10,556–27,092 |            0 |

Those figures describe the removed reference programs. Typed ownership did not make them
generated, and it does not imply support for an unrecovered source feature family.

## Controlled feature campaign

Of the 25 focused FCStd inputs under `.rescratch/sw/fcstd`, 22 reached the native vendor-loadable and
application-usable path. These three failed closed:

- `.rescratch/sw/fcstd/kit_boss_disjoint_revolve.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_front.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_top_midplane.FCStd`.

They require one or more unrecovered semantics: a Front-plane stepped pin, a mid-plane revolution,
or a disjoint pad-plus-revolution body history.

## Unsupported families in the full corpus

The audit recorded each type at most once per unsupported document. `native`, `reference`,
`extrusion`, and `fillet` are Kit timeline kinds used when a source object has no more specific
FreeCAD type identifier.

| source or timeline type      | documents |
| ---------------------------- | --------: |
| `App::FeaturePython`         |         3 |
| `App::GeometryPython`        |         2 |
| `Part::Box`                  |         9 |
| `Part::Compound`             |         1 |
| `Part::Cut`                  |         7 |
| `Part::Cylinder`             |         3 |
| `Part::Extrusion`            |         2 |
| `Part::Feature`              |         5 |
| `Part::FeaturePython`        |        11 |
| `Part::Line`                 |         1 |
| `Part::Mirroring`            |         2 |
| `Part::MultiCommon`          |         1 |
| `Part::MultiFuse`            |         4 |
| `Part::Offset2D`             |         1 |
| `Part::Part2DObjectPython`   |         6 |
| `Part::Plane`                |         1 |
| `Part::Sphere`               |         1 |
| `PartDesign::AdditiveBox`    |         1 |
| `PartDesign::AdditiveSphere` |         1 |
| `PartDesign::LinearPattern`  |         2 |
| `PartDesign::Pad`            |        16 |
| `PartDesign::Plane`          |         2 |
| `PartDesign::Pocket`         |         9 |
| `PartDesign::PolarPattern`   |         2 |
| `PartDesign::Revolution`     |        20 |
| `Path::FeaturePython`        |         4 |
| `extrusion`                  |        42 |
| `fillet`                     |        21 |
| `native`                     |        54 |
| `reference`                  |        54 |

`PartDesign::Pad`, `Pocket`, `Revolution`, `LinearPattern`, and `PolarPattern` in this table are
outside the exact profile, plane, termination, dependency, or operation sequences listed in the
recovered section; their type name alone is not sufficient for acceptance. The three
`Part::Cylinder` rows are likewise cylinders embedded in unrecovered multi-object histories, not
standalone primitives satisfying the exact cylinder gate.

## Assembly corpus result

All five FCStd documents detected as assemblies failed the portable native SLDASM contract:

- `.rescratch/out.FCStd`;
- `.rescratch/freecad/FreeCAD_1.1.3-Windows-x86_64-py311/data/examples/AssemblyExample.FCStd`;
- `re/solidworks/examples/Random/V8_engine.FCStd`;
- `re/solidworks/examples/Random/V8_engine/Conrod_2.FCStd`; and
- `re/solidworks/examples/Random/V8_engine/Piston_2.FCStd`.

The removed assembly writer had a typed zero-opaque core, which was itself a recorded payload, and
these inputs required unsupported component feature histories or assembly semantics.

## Completion boundary

The stream programs used by the accepted families had no opaque bytes, but each one was a recorded
payload: a typed re-encoding of one saved stream, re-emitted at its saved length with selected fields
overridden. They held 185,090 recorded field operations and were removed. A generative serializer is
the remaining SOLIDWORKS writer work, starting with a profile whose stream length and topology vary
with the input. Feature-semantic work also remains across the corpus, especially arbitrary sketch
profiles, multi-object primitive and Boolean Part histories, broader revolution modes, non-campaign
pattern histories, and the five real assemblies.

## Native box oracle

The removed standalone box program was not inferred from its internal decoder alone. Its output
was opened and rebuilt in SOLIDWORKS 2025 between healthy controls with zero load errors or
warnings, one solid body, `Sketch1`, `Boss-Extrude1`, volume 1,000 mm³, surface area 600 mm², and
centre of mass `(5, 5, 5)` mm. Independent live parameter drives on that generated file produced:

| parameter          | value | volume mm³ | centre of mass mm |
| ------------------ | ----: | ---------: | ----------------- |
| `D1@Sketch1`       | 20 mm |      2,000 | `(10, 5, 5)`      |
| `D2@Sketch1`       | 15 mm |      1,500 | `(5, 7.5, 5)`     |
| `D1@Boss-Extrude1` | 12 mm |      1,200 | `(5, 5, 6)`       |

The box-specific 14,855-byte `ResolvedFeatures` program contained 3,522 typed operations, and its
25,158-byte `Config-0` program contained 4,345 typed operations. Both tiled their reference streams
exactly with zero opaque spans. This shows SOLIDWORKS accepted the recorded program, not that the
program was generated.

## Native cylinder oracle

The removed standalone cylinder path used a separate, diameter-dimensioned circle program. Its
12,514-byte `ResolvedFeatures` stream contained 338 objects, 49 class definitions,
2,873 typed operations, 538 serializer owners, zero missing fields, and zero opaque spans.
The matching 25,158-byte `Config-0` stream reused the 4,345-operation field program and
specialized 29 typed fields for the circle's identities, bounds, cache metadata, radius, and depth.

A generated 5 mm radius by 10 mm high cylinder opened and rebuilt in SOLIDWORKS 2025 with zero load
errors or warnings, one body, `Sketch1`, `Boss-Extrude1`, volume 785.3981633974485 mm³, surface area
471.238898038469 mm², and centre of mass `(0, 0, 5)` mm. Independent live edits produced:

| parameter          | value |         volume mm³ |  surface area mm² | centre of mass mm |
| ------------------ | ----: | -----------------: | ----------------: | ----------------- |
| `D1@Sketch1`       | 16 mm | 2,010.619298297468 | 904.7786842338604 | `(0, 0, 5)`       |
| `D1@Boss-Extrude1` | 12 mm |   942.477796076938 | 534.0707511102650 | `(0, 0, 6)`       |

An independently generated 8 mm radius by 12 mm high FCStd also opened with one body, volume
2,412.74315795696 mm³, surface area 1,005.3096491487335 mm², and centre of mass `(0, 0, 6)` mm.
An off-origin generic circle was observed rebuilding at the origin; that case failed closed
and was not reported as lossless. A reverse-direction oracle proved that the high feature flag alone
is insufficient, then complete field tracing recovered the entire coupled history. After saved
path and document-name metadata are canonicalized, both reverse streams retained the normal 12,514-
and 25,158-byte widths with zero opaque spans. The generated negative-Z body opened and
rebuilt without warnings, and independent diameter and depth edits remained parametric. The removed
writer accepted strict origin-centred Front-plane reversed blind circles and rejected off-origin and
non-front variants.
