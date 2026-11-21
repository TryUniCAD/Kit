# SOLIDWORKS paired blank-drawing native comparison

The drawing oracle tools can compare two frozen generated blank drawings
at the same input and save paths. Prepare the packets with
`PrepareBlankDrawingPair.py`, then run the staged Windows observer with
the validated packet hash. The observer records the pristine controls on
both sides, a reduced native control, source immutability and each fresh
SOLIDWORKS process.

The cosmetic-thread comparison completed eight native phases on
SOLIDWORKS 2026 SP05.2. Both candidates opened, rebuilt and accepted their
scale edit. Both returned native save error 1 and left zero-byte targets.
All three controls saved and reopened cleanly. This comparison measures
one isolated field on a disclosed blank sheet.
[Command and result](../../../../../re/solidworks/records/DrawingSaveBoundary2026.md#paired-native-result)
