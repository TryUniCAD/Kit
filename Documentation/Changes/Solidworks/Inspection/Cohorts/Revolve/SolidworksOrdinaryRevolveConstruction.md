# Generate an ordinary revolved boss research candidate

The SOLIDWORKS 2026 research part builder constructs a rectangular contour, its construction centerline and a single ordinary boss revolve from semantic inputs. The revolve owns a model-fed line reference and a driving angular parameter. The file derives its profile and feature identity from the shared allocator and presents the angle in degrees in KeyWords.

Use `feature_kind="revolve"` with a principal-plane rectangular contour, `revolution_name`, `axis_start_m`, `axis_end_m`, `angle_rad` and `reverse_direction` in the existing fresh part request. The axis endpoints describe an upward line to the left of the contour in sketch coordinates. The mode supports a positive one-direction blind sweep through a full turn with degree presentation. [Construction rules and field evidence](../../../../../../re/solidworks/records/OrdinaryRevolvedBossConstruction2026.md).

Three independent generated candidates round-tripped all nine modeled streams with zero tails. The isolated process tests checked linked profile and line ownership, driving radians, metadata, input-dependent stream length and rejection of a crossing axis. The existing forward blind part and one-occurrence assembly bundle retained their native container hashes. [Process integration checks](../../../../../../tests/Convert/Solidworks/Research/Revolve/RevolvePartTests.py).

The first generated cohort opened with warning 32, had one feature problem and zero initial bodies, and failed forced rebuild in each case. Both controls passed. Set `inspect_regeneration_warning` in the diagnostic job to record model state before explicit rebuild and continue the investigation. A warning still fails the acceptance gate. [Baseline diagnostic](../../../../../../re/solidworks/measurements/2026/GeneratedRevolveRegeneration01.json) and [generated revolve inspector](../../../../../../re/tooling/sw2026/InspectGeneratedRevolves.py).

The corrected generator derives the selected axis reference's creation stamp from the sketch's own log state, including the native unset value for a sketch without logs. That single archive field changed across all three files. The corrected candidates opened without errors or warnings, rebuilt one solid and passed driving-angle edits for all three angle and direction cases. Both controls passed across five distinct processes and 75 numeric checks. [Load and reference identity diagnostics](../../../../../../re/solidworks/records/OrdinaryRevolvedBossLoad2026.md) and [measured intervention](../../../../../../re/solidworks/measurements/2026/GeneratedRevolveSketchLog02.json).

The first edited-save run kept all three edited angles, signed geometry and
one solid on clean fresh reopen. The exact tree comparison found one difference
at the empty material folder. SOLIDWORKS restored its standard caption on reopen.
Using the caption defined by the native English resource, all three candidates
kept their exact 20-node trees, edited angles and signed geometry on clean fresh
reopen. Both controls passed across eight distinct processes and 111 numeric
checks. [Edited-save diagnostic](../../../../../../re/solidworks/measurements/2026/GeneratedRevolveEditedPresentation03.json)
and [fresh-reopen result](../../../../../../re/solidworks/measurements/2026/GeneratedRevolveEditedReopen04.json).

Two independently authored held-outs passed the native tree, geometry, profile and driving-edit comparisons with the same generator. Both controls passed. The user-facing adapter remains read-only. [Preregistered method](../../../../../../re/solidworks/records/OrdinaryRevolveHeldoutProtocol2026.md) and [held-out measurement](../../../../../../re/solidworks/measurements/2026/GeneratedRevolveHeldout06.json).
