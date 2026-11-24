# SOLIDWORKS catalogue capture shutdown

Catalogue capture drains unused native COM wrappers on the thread that owns the
application. It runs this cleanup before requesting a normal application exit
and again after releasing the application reference. Batch captures use the same
cleanup between cases while retaining the owned application for the next case.
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
This evidence establishes the failing boundary. Verification on the six exact
cases and the interrupted batch is pending for the cleanup change.
[Shutdown finding](../../../../Gotchas/Research/Workers/SolidWorks/CatalogueCaptureExitObservation.md)
