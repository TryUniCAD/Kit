# Measured SOLIDWORKS revolve end modes

The ordinary native revolve writer covers the four measured Top-plane
rectangular profiles. The Mid Plane profile owns a total D1 and derives
its two half angles. The two Two Directions profiles retain distinct D1
and D2 owners in both rotation senses. The existing one-direction
profile retains its exact native bytes. Strict full and design-only
reads preserve the selected construction line and the same live drivers
through neutral JSON.

Use the SDK's `solidworks_native_measurement` option with the original
epoch and a `receipt` mapping of authenticated UTF-8 measurement
texts supplied by the caller. The required fields are
`generation_receipt`, `native_result` and `inspection_job`.
The [disclosed measurement record](../../../../re/solidworks/v2026/corpus/revolve/MeasuredEnd01/)
documents the qualified cases and their evidence. The SDK checks the
supplied data in memory before opening the destination.
The native report can use its original CRLF encoding or the exact
published LF equivalent. An empty binary sink needs the exact
`final_destination` from the corresponding request. Physical
files use the measured UNC path or its matching macOS share path.

These four disclosed files passed native opening, editable angle changes,
save and fresh reopen. The guarded SDK process matched every complete
file and ten logical streams with zero runtime input reads.
Native-saved styles and new archive digests require their own
qualification.
[Procedure and scope](../../../../re/solidworks/records/MeasuredOrdinaryRevolveEndPublication2026.md)


The shared complete suite checks the Mid Plane case and both signed Two
Directions cases through isolated SDK processes. The independent
structural reader uses different angles, rectangular profiles and Top
or Right supports. These neutral models exercise strict reading and
unmeasured output refusal.
[Reader boundaries and exact evidence](../../../../re/solidworks/records/MeasuredOrdinaryRevolveEndPublication2026.md#shared-queue-coverage)
