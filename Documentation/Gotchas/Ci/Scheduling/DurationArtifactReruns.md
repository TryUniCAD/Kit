# Duration artifact reruns

A report-job rerun keeps the workflow run ID and increments its attempt.
A fixed duration artifact name can therefore collide with the first successful report's upload.
The verifier can pass while the upload fails, which blocks acceptance.

Enable `overwrite` for both platform duration uploads.
These artifacts contain scheduling hints, not reusable test outcomes.
If replacement races with a history download, use fallback weights without consuming incomplete files.
See [runtime scheduling](../../../Changes/Ci/QueueRuntimeScheduling.md).
