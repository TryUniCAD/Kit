# macOS sandbox can hide worker process identity

## Expectation

The research supervisor records its held worker's process identity before releasing that worker.

## Actual behavior

In the restricted macOS execution sandbox, `Processes.process_start` returned `None` for the current Python process.
The supervisor refused worker release with `process identity unavailable before runner release`.
No reader or native CAD job started in that attempt.
The controller retained the exhausted one-attempt job as failed.

The same identity probe outside the sandbox returned the expected `ps:` creation timestamp.
The existing supervisor then started its offline worker successfully without any code or identity-check change.

## Workaround

Obtain execution approval for the existing supervisor outside the restricted sandbox.
Retain the failed controller result and submit a separate revisioned retry job.
Keep the worker's process gate, lease validation, cleanup and result checks enabled.

[Replay evidence](../../../../../re/DecodedReadWrite20261127/README.md) records the separate attempts and exact pinned SDK.
