# Catalogue pause needs pending work

The resume integration checks that pause stops new admission, active jobs can
settle, and resume adds receipts without replacing previously accepted ones.
Polling the supervisor log for its first finished event leaves time for the
supervisor to admit every remaining job while the pause command starts.

The Linux queue test on candidate `788def175085543d502fd56abfad9380360ff7ac`
saw one completed and eight queued jobs, then five completed and zero queued
at the pause. The active group drained to nine completed jobs, so resume
correctly produced the same nine receipts and the growth assertion failed.
[Linux shard and failure](https://github.com/TryUniCAD/Kit/actions/runs/44845500467/job/136664381226)

For the integration fixture, signal the first accepted settlement from inside
the supervisor process and hold it before the next admission. Release it only
when the genuine pause command publishes the catalogue's private pause marker.
The resumed process then has pending work to complete.
[Fixture](../../../../tests/Research/Inference/Scope/CatalogueResumeTests.py)
