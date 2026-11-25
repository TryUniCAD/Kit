# Isolate rejected SOLIDWORKS catalogue cases

The SOLIDWORKS catalogue checks every case after both owned native processes
finish. A case that fails verification keeps its native attempt files and exact
rejection reason. It has no accepted archive bundle. The controller releases
decoder jobs for the cases that passed independent reopen and verification.
It preserves their original bundle roles even when a neighboring case fails.

Use the existing SOLIDWORKS catalogue authoring command with a new run directory.
The catalogue result reports a rejected case as `failed` with
`native_rejection`. Its decoder remains blocked by the absent evidence.
Launch, shutdown, manifest, and unexpected infrastructure failures still retry
the whole native batch within the existing controller attempt limit. Forced
cleanup cannot authorize decoding.
[Catalogue authoring](../../../../Tasks/ResearchCommandLine.md#author-new-catalogue-samples)

In the earlier 62-case run, three thin-wall measurement failures withheld
nine cases across three batches. Individual checks of the preserved reports
found six companion cases with independently verified native evidence. The
separate wall-side repair passed thin walls in XY, YZ and XZ, including a
held-out 40 mm profile with a 2.6 mm wall. The shutdown replay also verified
recovery on the third fresh attempt after two native exit timeouts.

The controller and supervisor integration case checks that a withheld
artifact leaves its decoder unstarted and that a valid sibling bundle reaches
its own decoder. That process check uses retained transport fixtures and does
not attest native geometry. The original measurements remain in the
[shutdown evidence](SolidWorksCaptureShutdown.md) and
[thin-wall evidence](SolidWorksThinWallSide.md).
[Batch rejection finding](../../../../Gotchas/Research/Workers/SolidWorks/RejectedCatalogueBatchMember.md)
