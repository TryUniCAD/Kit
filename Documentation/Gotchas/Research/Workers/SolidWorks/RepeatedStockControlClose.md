# Repeated stock controls can stall between native cases

## Expectation

A healthy leading control should close before the next case starts in the same owned application process.

## Observed behavior

The three-case native batching proof at `4adb0278655f1fc9a760cd3df0648e7861f6b4a5` saved its first P01 baseline.
The next leading control measured the expected volume, then remained open.
A bounded read-only query to the recorded process-specific COM object returned one document, `example.SLDPRT`, and `CommandInProgress` false.
The second candidate had not been created.
The earlier written-recipe batch in `Discovery-20261124-201831` exhibited the same progress boundary and reached its 600-second phase deadline.

The existing hidden-document and `QuitDoc` path applied only to trailing controls.
Leading controls still used the ordinary `CloseDoc` path when they were the only open document.
The failed proof was stopped through its verified worker identity and retained separately.
No manually assisted attempt qualifies as native batch acceptance.

## Resolution and evidence

Use the existing hidden read-only close path whenever the control starts in an empty owned session.
The close still requires the exact stock path, read-only status, and a single open document.
Verify an empty document set after closing.
Native controls, geometry checks, independent reopen processes, and normal-exit checks remain required.
Fresh native verification is recorded in [paired-case batching](../../../../Changes/Research/Supervisor/Catalogue/PairedCaseBatching.md).
