# Preserve measured tree output from an immutable source snapshot

The [tree freeze](../../../../../re/solidworks/v2026/heldout/TreeWriterFreeze.json)
binds all 3,435 constructor and dependency files used by the two native-measured
predictions. Continued writer work must not reinterpret those measurements as
results from a newer implementation.

The existing remote process gate now restores only the frozen source blobs
from the exact Git tree. It verifies every blob, source membership and hash,
then regenerates the two original predictions from their committed neutral
requests in independent interpreters. It requires byte-identical output and
project imports inside the temporary snapshot. No native payloads, recorded
field operations or private reference observations enter the snapshot.

The original [prediction receipt](../../../../../re/solidworks/measurements/2026/TreeHeldoutProcessesE727.json)
and [native measurements](../../../../../re/solidworks/measurements/2026/TreeParityInspection01.json)
stay unchanged. The [remote regression receipt](../../../../../re/solidworks/measurements/2026/TreePinnedRegressionB26.json)
binds both artifact members to their original native-measured hashes. The
policy and native format job passed at the recorded revision. This is
regression evidence. The new source/writer pair still needs its own archive
and native acceptance checks.
