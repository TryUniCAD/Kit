# SOLIDWORKS catalogue capture shutdown

Catalogue capture gives each native phase a dedicated single-threaded COM
apartment. It drains unused wrappers before requesting application exit and
again after releasing the application reference. Batch captures use the same
cleanup between cases while retaining the owned application for the next case.
The apartment thread finishes before the PowerShell launcher waits for the
application process. Startup reads the executable path through the original
process handle while separately verifying the creation time and session.

A successful phase reopens the existing stock control as its sole read-only
document. It switches the owned application to program-controlled background
mode and requests the documented last-document exit through `QuitDoc`. If
the application remains responsive and confirms an empty session, the worker
also calls `ExitApp`. Failed phases still request `ExitApp` for cleanup.
If the process remains alive afterward, the launcher rechecks its creation identity
and verifies the recorded SOLIDWORKS frame belongs to it before posting a normal
window close. Both requests share the existing 30-second exit deadline. The
receipts record the native exit method and whether the frame close was posted.
The launcher still requires an observed normal exit through its original process
handle before continuing to a fresh reopen. Forced cleanup remains a failure.

Batch captures use the controller's existing three-attempt limit for the
single-case worker. Each attempt starts with a fresh native directory.
The controller retains failed attempts and only releases the dependent
decoder jobs after a batch passes independent reopen and normal exit.

Use the existing `kit run solidworks --author-samples` workflow and registered
native host. The catalogue binds each run to its starting source revision. To
exercise a changed worker, use a fresh run directory and the original case
parameters. The previous run retains its accepted receipts and failed attempts.
[Catalogue authoring](../../../../Tasks/ResearchCommandLine.md#author-new-catalogue-samples)

The reported run saved the first model with zero save errors or warnings on all
21 failed P04 attempts. The worker requested `ExitApp`, while the launcher never
observed the owned process exiting normally. Six cases exhausted their retries.
The first cleanup candidate recovered two cases and still reproduced the
timeout on the 7 mm cut-width case. The stock-control repair from PR #288
also reproduced that case's exit timeout in a combined local probe.
The dedicated apartment recovered the exact 7 mm cut case and its 11 archives
at `95afdb67740e377cc33882f12fb3e5a90d2558d1`. A boss-extrude control still
timed out twice. The owned process had a responding main window after its exit
request. The subsequent replay found that the Windows main-window lookup had
selected an embedded browser window. Closing the verified frame after `ExitApp`
and switching background control off before `ExitApp` still reproduced the
timeout.

At `8802a83fb0c8503cc7e979f977037af7d89ba015`, the exact 28 mm cut-extrude
case passed its first attempt on SOLIDWORKS 34.4.1.1011. Both phases recorded
the last-background-document request followed by a verified-frame close and a
normal process exit. The two PIDs were distinct and neither required forced
cleanup. The worker independently reopened 11 archives and the decoder
recorded its results. The catalogue result SHA-256 is
`66578828b46645927feb6686b0a72a2c31eb6f870bfde6b0475ed6a01385ecd7`.

The combined replay at local revision
`aae8b6498fa7e09e70ea0d1d3369705133ce884e` includes the shared shutdown
code and the stock-control batching repair from PR #288. Two three-case
batches covered the other five previously failed cut-extrude cases and a
boss-extrude control. All six cases passed on their first attempt. Four
independently owned processes exited normally, 63 archives passed the native
checks, and all six decoder jobs recorded their results. The driving-dimension
singleton saved its baseline and posted the frame close, but its process
remained alive at the deadline. The worker forced cleanup and withheld the
singleton from decoding. The result SHA-256 for this replay is
`68a03e331f2e04f67992a87b45ed524008e67523010fe3e969ff637319ed8e3a`.
All six original cut-extrude failures passed across the two replays. The
singleton exposes an intermittent native shutdown failure. A second verified
window close did not recover it. The standalone worker recorded a forced
cleanup on its first attempt, then verified six archives and both normal
process exits on its second. The dependent decoder recorded its results.
The standalone result SHA-256 is
`2af0c8228f3e465ce3ac226e803e7460984288d4867afba7de8f59103f8bc445`.
At `67c44a8a54c3271198135a1d0c90e2f6d944a8a1`, both singleton phases
reported an empty session after `QuitDoc` and exited after the vendor
`ExitApp` call without a window close. Six archives passed on the first
attempt and the dependent decoder recorded its results. The final worker
replay and batch retry are under native verification.
The singleton probe result SHA-256 is
`162b00d1577164ab84f1d3b49c698c9d7870a75fff3d93ff363c97f180557f21`.

The written-recipe replay reached both native phases and both processes exited
normally. It saved and reopened 30 archives. Native admission failed because
the thin-extrude one-sided wall extended opposite the specified sketch side.
The offset-start and two-direction geometry checks passed on the preserved
receipts. The catalogue result SHA-256 is
`1b6e1e6bfbde418c66644f6c73ef698442d76c986e224d953da40ee6a8808c5a`.
The separate thin-wall correction recovered all three recipes and their
decoder jobs. [Thin-wall replay and receipts](https://github.com/TryUniCAD/Kit/pull/291)

The shared Windows process probe checks that a window belonging to another
live process is refused. It also checks that a verified window receives just
one close request while its owning process remains alive. The exit receipt records
the observed process state separately from the request.
[Shutdown finding](../../../../Gotchas/Research/Workers/SolidWorks/CatalogueCaptureExitObservation.md)
[Starting process image finding](../../../../Gotchas/Research/Workers/SolidWorks/StartingProcessModuleLookup.md)
[SOLIDWORKS frame finding](../../../../Gotchas/Research/Workers/SolidWorks/HiddenFrameWindowSelection.md)
[SOLIDWORKS welcome finding](../../../../Gotchas/Research/Workers/SolidWorks/WelcomeWindowClose.md)
