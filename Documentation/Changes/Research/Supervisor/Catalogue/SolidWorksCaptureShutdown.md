# SOLIDWORKS catalogue capture shutdown

Catalogue capture gives each native phase a dedicated single-threaded COM
apartment. It drains unused wrappers before requesting application exit and
again after releasing the application reference. Batch captures use the same
cleanup between cases while retaining the owned application for the next case.
The apartment thread finishes before the PowerShell launcher waits for the
application process. Startup reads the executable path through the original
process handle while separately verifying the creation time and session.
If the empty owned session remains alive after `ExitApp`, the launcher verifies
its creation identity again and asks the SOLIDWORKS frame recorded by the COM
client to close. It checks the frame's process identity before posting the
request. Both requests share the existing 30-second exit deadline. The owner
receipt records whether the second close request was posted.
The launcher still requires an observed normal exit through its original process
handle before continuing to a fresh reopen. Forced cleanup remains a failure.

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
selected an embedded browser window. Verification of the guarded SOLIDWORKS
frame request is pending.
[Shutdown finding](../../../../Gotchas/Research/Workers/SolidWorks/CatalogueCaptureExitObservation.md)
[Starting process image finding](../../../../Gotchas/Research/Workers/SolidWorks/StartingProcessModuleLookup.md)
[SOLIDWORKS frame finding](../../../../Gotchas/Research/Workers/SolidWorks/HiddenFrameWindowSelection.md)
