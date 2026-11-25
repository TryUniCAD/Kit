# Four-byte cylinder snapshots refuse re-emission

## Expectation

A complete typed native read can appear to imply that the same file can be written.

## Observation

Seven rim-fillet sources decoded but refused re-emission at the specialized snapshot-header guard.
The [header census](../../../../re/Fusion/RimFilletPack/Evidence/HeaderCensus.json) identifies integer width four as their only guard difference.
The specialized writer requires width eight; the generic geometry serializer supports both widths.
Five other source files used supported representations and reconstructed.

## Workaround

Keep the refusal and source bytes. Do not normalize the width or delete the snapshot.
A repair must preserve the complete typed model and pass native reopen, edit and restore checks.
This checkpoint includes no unqualified production repair.
