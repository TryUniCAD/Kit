# Generate an ordinary revolved boss research candidate

The SOLIDWORKS 2026 research part builder constructs a rectangular contour, its construction centerline and a single ordinary boss revolve from semantic inputs. The revolve owns a model-fed line reference and a driving angular parameter. The file derives its profile and feature identity from the shared allocator and presents the angle in degrees in KeyWords.

Use `feature_kind="revolve"` with a principal-plane rectangular contour, `revolution_name`, `axis_start_m`, `axis_end_m`, `angle_rad` and `reverse_direction` in the existing fresh part request. The axis endpoints describe an upward line to the left of the contour in sketch coordinates. The mode supports a positive one-direction blind sweep through a full turn with degree presentation. [Construction rules and field evidence](../../../../../../re/solidworks/records/OrdinaryRevolvedBossConstruction2026.md).

Three independent generated candidates round-tripped all nine modeled streams with zero tails. The isolated process tests checked linked profile and line ownership, driving radians, metadata, input-dependent stream length and rejection of a crossing axis. The existing forward blind part and one-occurrence assembly bundle retained their native container hashes. [Process integration checks](../../../../../../tests/Convert/Solidworks/Research/Revolve/RevolvePartTests.py).

The diagnostic wrapper schedules fresh native open, rebuild and in-memory driving-angle measurements with bracketing controls. Saving an edited candidate and verifying it on a fresh reopen remain pending. Two independently authored held-out inputs remain sealed. The user-facing adapter remains read-only. [Generated revolve inspector](../../../../../../re/tooling/sw2026/InspectGeneratedRevolves.py) and [native source lock](../../../../../../re/solidworks/v2026/heldout/OrdinaryRevolveSourceLock.json).

The first native inspection opened all three generated files with zero errors
and warning 32 between healthy controls. The diagnostic job can specify
`inspect_regeneration_warning` to record model state before explicit rebuild
and continue measuring geometry and angle edits. A warning remains a failed
acceptance gate.
