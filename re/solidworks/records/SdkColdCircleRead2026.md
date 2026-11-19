# Strict cold-circle reading for SOLIDWORKS 2026

The normal registered writer produced a valid native circle part that the default strict SDK reader rejected with `SLDPRT contains no readable Parasolid payload`. The reader admitted the existing cold prism, pocket and revolve histories, but had no corresponding circular-boss branch. The new bounded route reconstructs the two profiles already qualified by the public circle writer. It changes no writer bytes or registrations.

Task: `B04-SW2026-COLD-CIRCLE-READ`. Owner: `/root/assembly_occurrence`; root owns integration, shared registers and the vendor oracle. Delivery: PR #121. Dependencies: the existing circle writer, typed local-circle and live extrusion owners, complete Config/Resolved/CMgr admission, and shared `BuildCircular`. Exit: exact normal-entry output succeeds through default strict reading with complete owner, shape and driver checks; malformed counterparts refuse; existing geometry reads remain identical. This is an SDK read result. It adds no native concentric mate or persistent face identity qualification.

## Original failure and exact boundary

The frozen source snapshot contains 4,608 SDK and explicit fixture files. Its baseline manifest is SHA-256 `f018d720af14874b62fd8fd3354099d46e3fe7abc11c88fd0a83ee2e8c3d7f63`. The original front output is 8,348 bytes, SHA-256 `84d10de57047dc4217fb3cf4c676c845a543b67c6caa86ef6232668ffe3e37ee`; canonical neutral document digest is `5f53f98109e1fb2709220106f8e3d34df65b385def53ec539c8891b682bda143`. It is emitted through normal `write_document`, the default registry and the existing `solidworks.sldprt` stream destination. The research clock is fixed to authored epoch 1765500071; no writer result or native behavior is mocked.

Both original public profiles reproduce the strict refusal in independent baseline processes. The same generated payloads then pass the candidate's default `open_document` route. The public writer still admits exactly its prior qualified profiles: Front Plane, diameter, forward blind; or Top Plane, radius, reversed blind. This change adds no writer end, datum, option or destination mode.

## Admission and actual owners

`IsCacheAbsent` retains the existing physical stream and payload boundary. The new branch is reached only after the existing cut and revolve branches and only for an actual typed circle. The ordinary version-19000 linked graph remains mandatory. The branch reuses:

- `CheckGeometryState`, `PrismNodes` and `CheckPrismRoots` for complete nonprovisional grammar, whole feature inventory and absence of detached or extra owners
- `CheckPrismRoot`, `CheckPrismMgr` and `CheckPrismRels` for the actual empty body/ghost managers, configuration, model modes and relation graph
- `ReadExtrude` for actual profile parents, start, active depth handle, parameter and direction
- `CheckPrismProf`, `CheckPrismPlane` and `ReadPrismFrame` for the ordinary profile, all three real principal datums, origin and exact local-to-model frame
- `ReadLocalCirc` for the actual circle seam and centre slots, permanent marks, fixed-centre relation, radial mode, live parameter and display owner
- `ReadPrismParam` for all four distinct end-display/dimension/parameter identities, positive active depth, equal inactive length and absent draft intent

The added class inventory contains the ordinary radial classes and `sgEntHandle`. That base handle belongs to the generated radial graph; it is an existing serializer class, not a new captured field layout. Extra classes remain closed.

The new radial guard rejects alternate/external parameter state. The new end guard rejects reference starts, draft controls and selected termination geometry. The first public mode guard retains the two measured support/driver/direction combinations. Additional profiles, configurations, body scopes, stored atoms, nonordinary starts, partial histories and unsupported nodes return the existing strict failure.

The existing prism boss-state checks are moved intact to a shared helper; their exact error text and predicates remain unchanged. Geometry diagnostic creation is factored into a shared helper so the main reader remains within the declaration-size rule. Existing prism, pocket and revolve messages are preserved. The circle diagnostic uses `method=typed_parametric_circular_boss`, records exact native profile/radial/depth/boss spans and signed stations, and explicitly reports `native_kernel_identity=false`.

## Derived geometry and identity

`BuildCircular` receives the validated native circle, actual principal frame and signed blind stations. It produces one closed solid with three faces, two periodic rim edges and two vertices. Volume, area, cylinder axis, radius, both cap origins and all six bounds are compared to independent neutral formulas. Radius and depth edits construct new inputs and new files through the same normal registry boundary.

The returned B-rep owns its actual `DesignBody.id`; its face and surface strings are new neutral topology identities. They are not native kernel tags, `FACE_ID_2001`, atom IDs or `moEntityIdRep_c` values. They cannot be passed to a concentric native endpoint constructor. The circle part retains its actual generated profile arc and boss owners, and the existing occurrence chain can be reused once circular assembly bounds and native face references are independently qualified. Those future construction obligations remain open.

## Process proof

[Sanitized receipt](../measurements/2026/SdkColdCircleRead01.json), SHA-256 `51e9f1248544a96278aede442018b0cd438112c38bb5f1ed6e4d3f3ce338d0e3`, binds raw result SHA-256 `88e3f2b93c6b083481b87c38fc54ed0a314c6271ce93f32de400d2b4e53fab62` and the complete before/after source closure.

There are 33 fresh processes: seven neutral-input processes and 26 guarded build/read processes. The latter contain two original refusals, six successful default strict circle reads, twelve deliberate malformed refusals and six legacy reads forming three complete equality pairs. The malformed archives independently change draft, inactive length, selected scope, radius agreement, actual support or profile-parent ownership for each circle profile. All refuse. Both positive profiles repeat identically. Each profile also passes a separately authored radius/depth edit.

The three legacy inputs are independently generated prism, blind pocket and reversed partial revolve histories. Their complete output bytes and canonical neutral document serializations are identical before and after the reader change. All 26 read/build workers report zero runtime data-file reads. Sources and scripts remain unchanged throughout the final run. No CAD process, original source file or hidden input is used.

All 17 SDK files pass AST/Black, Ruff, scoped strict Mypy, scoped strict Pyright and steering. The recorded-payload scan is clean across 4,599 SDK files. All 20 delivered Python files parse, and 262 relative documentation links resolve. Pyright reports zero source errors and retains three unsupported-setting notices inherited from repository configuration. Black's research-exclusion expression also matches the suffix of `Core/`; the explicit formatting run overrides that path filter while preserving the formatter rules. [Formatting gotcha](../../../Documentation/Gotchas/Python/BlackCorePathsNeedExplicitFormatting.md).

The first partial process deck stopped in a negative-input author: it asked a decoded principal-plane node for constructor-only `f34c`. The corrected negative chooses another real decoded plane by its actual feature ID. The twelve refusal outcomes are from the corrected final deck; the first deck is retained separately and receives no successful coverage credit. [Decoded-owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/DecodedPlaneChecksNeedActualDatumOwners.md).

## Reproduction

The private handoff pins the exact candidate/baseline code roots, scripts, source hashes and requests. Run [RunColdCircleRead.py](../../tooling/sw2026/RunColdCircleRead.py) with the two immutable roots and a fresh output directory. The script exercises real normal-entry writes/reads and existing SDK constructors in separate processes; it does not call a unit-test runner, a CAD runtime or a vendor oracle.

This result repairs the strict read boundary for the existing public writer profiles. It does not establish arbitrary circular-source equivalence, original held-out conversion, generated native cylinder references, concentric mate writing or new vendor acceptance. Those remain separate parts of PR #121.
