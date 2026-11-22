# Republish measured offset-plane readbacks

The SOLIDWORKS SDK can republish the measured cache-free principal offset
datum, centred radius-driven sketch and forward blind boss from strict
full or design-only readback. Neutral JSON preserves the same write inputs.
Use the exact presentation, creation event, locator and native receipt from
the [measured offset options](SolidworksMeasuredOffsetPlanes.md).

The writer derives the constructor inputs from the actual selected
principal plane, signed distance, fixed circle centre, radius and boss
depth. It verifies the whole archive against the native receipt and
compares the complete untouched source with a strict reread before
publishing. Changed source state, receipts from a different cohort and the
tested native-saved histories refuse before the destination changes.
[Offset readback units](../../../../Gotchas/Conversion/Solidworks/Model/ReferencePlanes/OffsetReadbackUsesMetres.md)

The [guarded receipt](../../../../../re/solidworks/measurements/2026/SdkOffsetColdReadback01.json)
records two fresh SDK processes per disclosed Front, reversed Top and Right
part. All 72 stream publications through the registry, direct writer and
adapter reproduce the full native-measured bytes. The same processes
verify 144 refusals and zero runtime input file reads. The earlier native
measurements still supply the application evidence. This check adds no
new held-out cases or support for warm saved history.

Run the verification from the repository with
`python3.14 -I -B re/tooling/sw2026/offset_plane/ProveOffsetReadback.py --disclosure /path/to/disclosed-packets`.
