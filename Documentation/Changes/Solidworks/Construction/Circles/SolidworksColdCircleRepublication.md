# Republish exact measured cold circle bosses

The normal SOLIDWORKS part writer now accepts the strict SDK readback of
the measured cache-free fixed-centre circle profiles. Both default reads
with analytic B-rep and `include_brep=False` design-only reads can re-enter
the same measured writer. The original sketch retains its separate native
centre point and the boss retains each distinct active depth.

Use the existing `solidworks_native_measurement` envelope with the exact
offline report and creation event. Supply the measured logical path for a
stream or the matching destination for a file. The writer builds a new
archive from the linked neutral point, radial driver, support and depth
owners. It compares the entire strict source projection and the measured
file hash before publishing anything.

Six independently disclosed native-tested parts pass both strict reader
modes, 48 complete byte-exact normal re-publications and 108 unchanged
output refusals. Native-saved circle history and edited, unmeasured files
remain outside this scope.
[Proof and exact scope](../../../../../re/solidworks/records/SdkColdCircleRepublication2026.md)
