# Conversion SDK completion roadmap

Kit has working SDK infrastructure and qualified format subsets.
It does not yet provide complete editable conversion across its intended CAD families.
The next product milestone is a measured, editable SOLIDWORKS ↔ Fusion conversion through the public SDK.

Use the [conversion backlog](Documentation/Maintenance/ConversionBacklog.md) for task IDs, ownership, dependencies, open PRs and completion evidence.
That register is the entry point for available work.
[PR #158](https://github.com/TryUniCAD/Kit/pull/158) supersedes PR #94 and maintains the research step register.
Read the linked PR and its current head before claiming a task.

## Current position

This snapshot describes main `e04e7b78699d3f567409937007b00b567620078a`, inspected on 2026-11-15.
Open PR work is listed separately in the backlog.
The previous 22/100 estimate is retired because it counted historical capabilities that no longer describe the production adapter.
No replacement percentage is claimed without a complete acceptance matrix.

| Family                  | Production position at this revision                                                                       | Remaining product requirement                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| SOLIDWORKS              | Part and assembly reader and partial drawing reader.                                                    | Native part, assembly and drawing output, broader semantic reads and qualified editable routes.     |
| Fusion                  | Public reader and writer for qualified parameter, circle, rectangle, cylinder, cuboid and frustum graphs.  | General portable feature graphs, broader schemas, configurations and qualified cross-format routes. |
| FreeCAD                 | Archive reader and writer with geometry, feature and assembly paths.                                       | Per-version semantic coverage and measured acceptance for each claimed conversion direction.        |
| CATIA V5                | Part/product adapter with bounded native interpretation and preservation paths.                            | Complete geometry, parametric history and independently measured native conversion.                 |
| NX                      | No production adapter on this main revision. PR #115 adds native research and adapter work.                | Qualified semantic reads and independent editable writing.                                          |
| Creo                    | No production adapter on this main revision. PR #117 adds PSB research and adapter work.                   | Qualified semantic reads and independent editable writing.                                          |
| Rhino                   | No production adapter on this main revision.                                                               | Format/version contract, reader, writer and target acceptance.                                      |
| AutoCAD                 | No standalone production adapter on this main revision. Fusion drawing codecs are a separate bounded path. | Format/version contract, neutral drawing model and qualified standalone routes.                     |
| Kit JSON and shared SDK | Neutral model, serialization, discovery, conversion API, CLI and packaging exist.                          | Complete route evidence, operational hardening, user evaluation and release qualification.          |

Registration, same-format reconstruction and retained native bytes do not establish cross-format editability.
See [format selection](Documentation/Tasks/SelectFormat.md) and the [Fusion public contract](Documentation/Changes/Fusion/Adapter/FusionPublicAdapter.md).
The [SOLIDWORKS guide](Documentation/Reference/Adapters/Solidworks.md) documents the production write restriction.
PR #121 adds the generative line-loop blind boss writer and four independently qualified fixed-centre circle profiles. [Line-loop writer evidence](Documentation/Changes/Solidworks/Construction/SolidworksNativePartWriter.md) · [Blind circle evidence](Documentation/Changes/Solidworks/Construction/SolidworksCircleWriterRegistration.md) · [Mid-plane and two-direction evidence](Documentation/Changes/Solidworks/Construction/SolidworksCircleEndWriterRegistration.md)
The same PR qualifies ordinary partial rectangular two-direction boss revolves on canonical Top and Right planes, with two editable angular drivers. [Revolve writer evidence](Documentation/Changes/Solidworks/Construction/Revolve/SolidworksTwoDirectionRevolveWriting.md)
The square Mid Plane and Two Directions boss profiles retain their explicit equal-length sketch relation through native edits and normal SDK output. [Square revolve evidence](Documentation/Changes/Solidworks/Construction/Revolve/SolidworksSquareRevolvePublicParity.md)
The same PR adds normal geometry-only writing for one periodic cylinder or axis-aligned rectangular solid, with explicit B-rep and configuration transfers. [Periodic cylinder writer](Documentation/Changes/Solidworks/Construction/SolidworksPeriodicCylinderWriter.md) · [Rectangular solid writer](Documentation/Changes/Solidworks/Construction/Parts/SolidworksBareRectangleImport.md)
The two measured generated planar imports also round-trip through the normal SDK from full strict readback and neutral JSON. [Measured import round trips](Documentation/Changes/Solidworks/Construction/Parts/SolidworksColdImportRoundTrip.md)
The same PR adds normal writing for one explicit local width-to-depth equation on an origin-anchored Front Plane rectangular blind boss. [Local equation writer evidence](Documentation/Changes/Solidworks/Construction/SolidworksPublicWidthDepthWriter.md)
Its normal writer also reproduces both independently measured signed Top Plane rectangles with a fixed corner, two editable sketch dimensions and a reversed blind depth. [Top rectangle evidence](Documentation/Changes/Solidworks/Construction/Part/SolidworksExplicitTopRectangleOrigin.md)
The principal-plane thin revolve writer passed all four independent wall modes in native edits and fresh reopens. The earlier frozen public evaluation reproduced the same four files. The integrated SDK publishes six measured disclosed fresh neutral cases and strict cold reads retain their typed editable history and analytic solids. [Thin native evidence](re/solidworks/measurements/2026/SdkThinRevolveHeldoutNative01.json) · [Current measured thin publication](Documentation/Changes/Solidworks/Construction/Revolve/SolidworksMeasuredThinPublication.md)
The strict saved reader also retains editable thin revolve drivers and verified native solid ownership. The normal selected-revolve writer reproduces both pre-writer locked, native-tested candidates exactly. The cases retain both solid identities, actual stock selection, feature tree and editable D1 through the controlled native comparison. Four public path and stream cases also pass strict cold reads, and six saved reads reproduce 12 linked streams. [Saved thin revolve](Documentation/Changes/Solidworks/Reading/Parts/SolidworksThinSavedRead.md) · [Selected revolve writer](Documentation/Changes/Solidworks/Construction/Revolve/SolidworksSelectedRevolvePublic.md)
The normal strict reader also covers the measured saved Standard sweep, with independent Section and Path drivers and the verified periodic solid. Design-only reads still validate the physical result. [Saved sweep evidence](re/solidworks/records/AggregateSavedSweepRead2026.md)

The measured cache-free Standard sweep also supports strict editable readback and exact republication from full or design-only neutral JSON. [Cold sweep evidence](re/solidworks/records/SdkColdSweepReadback2026.md)
PR #121 also binds normal flat assembly output to the authenticated exact measured coincident and driving-distance pair. Other principal-plane groups and initially satisfied perpendicular assemblies retain separate internal construction and native evidence. [Measured planar assembly](Documentation/Changes/Solidworks/Construction/Assembly/SolidworksAuthenticatedPlanarBundle.md) · [Perpendicular assembly evidence](Documentation/Changes/Solidworks/Archive/Assembly/Groups/SolidworksPerpendicularRegistryQualification.md)
The scoped rigid nested writer uses owned rectangular blind-boss leaves and preserves repeated subassembly targets. Both pre-writer locked hierarchies passed controlled native depth edits and fresh reopens. Public file outputs match the disclosed native-measured bundles. [Nested assembly evidence](Documentation/Changes/Solidworks/Construction/Assembly/SolidworksRigidNestedAssemblyWriting.md)
The SDK writes one neutral, unlinked ANSI A landscape drawing with measured native scale edits, saves and fresh reopens on two independently locked inputs. The strict reader reconstructs the exact generated container and its typed layout and settings. The SDK and CLI regenerate a canonical generated blank at a new destination, with two held-out native rewrite lifecycles. [Canonical rewrite evidence](re/solidworks/measurements/2026/BlankRewriteHeldoutNative01.json) [Public blank drawing evidence](Documentation/Changes/Solidworks/Construction/SolidworksPublicBlankDrawingWriter.md) · [Strict reader evidence](re/solidworks/measurements/2026/SdkGeneratedBlankStrictRead01.json)
It adds typed readback for a solved perpendicular mate, native part properties with a verified empty advanced owner, and guarded prism geometry recovery. [Perpendicular read](Documentation/Changes/Solidworks/Archive/Assembly/SolidworksPerpendicularReaderOwnership.md) [Empty property owner](Documentation/Changes/Solidworks/Inspection/Properties/SolidworksEmptyAdvancedPropertyRead.md) [Typed prism read](Documentation/Changes/Solidworks/Inspection/Parts/Geometry/SolidworksTypedPrismReconstruction.md)
The scoped native part reader also binds one cache-backed solid to its actual name and design-body identity. [Native body read](Documentation/Changes/Solidworks/Reading/Names/SolidworksNativeBodyNames.md)
The measured single-edge angle-distance chamfer publishes both exact signed artifacts. The strict saved reader retains both live dimensions and the actual bevel's body and rollback owners. [Angle-distance chamfer evidence](re/solidworks/records/ChamferAngleDelivery2026.md)
The saved oblique linear-pattern reader preserves the finite hinge dependencies and the real angular driver. Three contained saves retain the editable pattern controls and the linked single solid. [Saved angular pattern evidence](Documentation/Changes/Solidworks/Reading/Patterns/SolidworksAngularPatternRead.md)
The normal SDK publishes the exact disclosed contained oblique pattern archives with their matched offline native receipts. [Measured publication](Documentation/Changes/Solidworks/Construction/Patterns/SolidworksMeasuredPatternPublication.md)

The corresponding cache-free contained oblique patterns also reconstruct through the normal strict path and stream reader. Both signed directions, separate pitch and count states, and the ordinary single selected configuration are verified. [Cache-free pattern evidence](Documentation/Changes/Solidworks/Reading/Patterns/SolidworksColdAngularPatternRead.md)

The scoped saved two-stock reader retains two independent blind bosses and their live D1s, one explicitly selected through-all cut, and two atom-linked final solids. [Saved two-stock read](Documentation/Changes/Solidworks/Reading/Parts/SolidworksSavedTwoStockRead.md)
Strict inspection reads the scoped rectangular inward open shell in its fresh and saved states. Native shell writing remains gated. [Open-shell readback](Documentation/Changes/Solidworks/Inspection/Parts/SolidworksColdOpenShell.md)
The cache-free reader reconstructs the corresponding two solids for the proven Front and Right rectangular profile and explicit circular through cut. [Cache-free two-stock read](Documentation/Changes/Solidworks/Reading/Parts/SolidworksColdTwoStockRead.md)
The writer generates that bounded neutral two-stock profile with both editable depths and the explicit Front-stock selection. Two pre-writer locked native comparisons passed. Publication requires their exact corrected receipt, measured locator and independently regenerated full archive. [Measured selected two-stock publication](Documentation/Changes/Solidworks/Generation/Extrusion/ThroughAll/SolidworksHeldoutSelectedStockPublication.md)

FreeCAD sketch visibility and verified legacy-carrier replay reached main at `533970231`. [FreeCAD sketch changes](Documentation/Changes/Freecad/FreecadHiddenSketchesStayActive.md)

## Destination

A fully functional release covers all nine CAD families above through one documented public SDK and CLI.
Every claimed input type, vendor version, feature family and conversion direction has explicit scope and acceptance evidence.
The release matrix must identify unsupported combinations before a conversion starts.
An unsupported route remains unfinished roadmap work and fails explicitly at runtime.

Each supported route must meet every [CAD success criterion](Documentation/Reference/Operations/CadSuccessCriteria.md).
Conversion uses no CAD runtime or donor data.
It preserves geometry, editable history, sketches, dimensions, constraints, expressions, materials and applicable assembly, configuration and drawing semantics.
Target applications must open, rebuild and measure the output correctly.
Independent driving edits, restoration, save and fresh-process reopen must pass on held-out inputs.
Source and target controls must bracket the measurements.

The release also needs reproducible installation, bounded resource use, secure file handling and clear failure reports.
Documentation and CLI tasks must be evaluated by their intended users.
Completion concerns a published version matrix, not every future vendor release.
Choosing that matrix is backlog task B01, not permission to discard required source information.

## Ordered milestones

| Milestone                                 | Work and dependencies                                                                                                | Evidence required to finish                                                                                                               |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| M0: establish the baseline                | B01 records file types, versions, features, fixtures and directional routes. Maintain this roadmap and PR ownership. | Every family and intended route has a supported, unsupported or unverified entry with evidence and an owner.                              |
| M1: qualify the first paired designs      | B02 qualifies the paired designs using independent source evidence on PR #158.                                          | Qualified initial sketches, bosses and cuts preserve every required relation. Reserved holdouts remain independent.                       |
| M2: deliver the first editable conversion | B03–B05 compare graphs, prove field rules, build portable writers and validate both directions.                      | SOLIDWORKS → neutral → Fusion and Fusion → neutral → SOLIDWORKS pass the public SDK and all applicable CAD criteria.                      |
| M3: cover ordinary part histories         | B06 expands sketches, references, operations, geometry and historical schemas. Integrate B08's existing format work. | Each feature/version extension has held-out, editable target acceptance. No required native semantics remain opaque on a supported route. |
| M4: cover complete documents              | B07 adds assemblies, mates, configurations, external references and drawings.                                        | Component resolution, placements, constraints, variants, dimensions and model links survive conversion and edits.                         |
| M5: complete all intended families        | B09 extends qualified readers and writers to every family. B12 closes the directional route matrix.                  | Every promised route and version passes full preservation and independent target acceptance, including failure cases.                     |
| M6: qualify the release                   | B10, B11, B13 and B14 complete user evaluation, packaging, security and operational evidence.                        | Published support matrix, reproducible release, passing required CI/reviews and merge-group acceptance.                                   |

M0 and user-facing improvements can proceed alongside the conversion critical path.
Each broader format can advance when its own prerequisites are available.
M5 still depends on complete-document acceptance for every promised route.
Do not delay narrow qualified releases until every family is complete.
Label each release with its actual supported matrix and remaining roadmap gaps.

## Next action

Continue **B02** using the [step register on PR #158](https://github.com/TryUniCAD/Kit/blob/8509332301a665bf0e618f00089e185c8c3c7cd3/Documentation/Reference/Research/AutomationSteps.md).
PR #94 reported native Fusion observations for P01–P04.
Check those observations against the pinned source captures before accepting them as independent evidence for A02d.
Use the accepted evidence to qualify the sketches, bosses and cuts in A04c and A05c before comparing graphs in A06.
Keep P05 reserved for independent validation.

The next independent task outside that programme is **B01: publish the supported version and route matrix**.
It can proceed while native evidence is unavailable.
It must reuse current adapter facts and PR ownership rather than create a second research plan.

## Maintenance

Update the backlog whenever a task is claimed, changes scope, becomes blocked, opens a PR or gains completion evidence.
Update this roadmap when a milestone or the production support boundary changes.
Keep implementation status in its owning register and link it here.
An open PR, successful decode, green PR check or application screenshot alone never completes a conversion milestone.
Follow [AGENTS.md](AGENTS.md) and the [documentation review procedure](Documentation/Maintenance/Review.md).
