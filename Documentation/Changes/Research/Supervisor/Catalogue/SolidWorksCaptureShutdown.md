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
mode and requests the documented last-document exit through `QuitDoc`. Failed
phases still request `ExitApp` for cleanup. If the process remains alive after
the successful phase's exit request, the launcher rechecks its creation identity
and verifies the recorded SOLIDWORKS frame belongs to it before posting a normal
window close. Both requests share the existing 30-second exit deadline. The
receipts record the native exit method and whether the frame close was posted.
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
Broader paired and written-recipe verification is in progress.

The shared Windows process probe checks that a window belonging to another
live process is refused. It also checks that a verified window can receive the
close request while its owning process remains alive. The exit receipt records
the observed process state separately from the request.
[Shutdown finding](../../../../Gotchas/Research/Workers/SolidWorks/CatalogueCaptureExitObservation.md)
[Starting process image finding](../../../../Gotchas/Research/Workers/SolidWorks/StartingProcessModuleLookup.md)
[SOLIDWORKS frame finding](../../../../Gotchas/Research/Workers/SolidWorks/HiddenFrameWindowSelection.md)
