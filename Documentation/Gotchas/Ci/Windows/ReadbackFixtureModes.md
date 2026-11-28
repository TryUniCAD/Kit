# Readback cache and prepared capture need both fixture modes

Expected: preparing a DLL before dispatch retains the source-keyed cache across test processes.

Observed: PR #121 used explicit compile and capture parameter sets.
Main added independent cache warm-up and contention checks.
Selecting either script version during the merge would remove the other caller contract.

The merged script accepts cached warm-up, explicit prepared output and prepared capture.
Preparation warms the shared cache before its bounded copy process.
Capture loads the prepared DLL and performs no compilation.
The process regression verifies cache contention, invalidation and exact prepared-copy bytes.
Readback queue cases verify the capture path through the actual listener and dispatch processes.

See [the merge record](../../../Changes/Ci/Testing/SolidworksReadinessFixtureMerge.md).
