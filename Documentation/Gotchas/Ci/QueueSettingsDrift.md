# Queue settings drift

The manifest's batching and concurrency values might appear to describe the running queue.
The live `Protect` ruleset observed on 22 November 2026 differed from the manifest.
It allowed 25 candidate builds, required two merge entries, and allowed a ten-minute minimum-entry wait.
The manifest already required one merge entry and zero wait before the scheduling repair.
Changing the manifest therefore cannot activate either fix.

An authorized administrator must update the existing ruleset's queue parameters separately.
Preserve unrelated protections and read the accepted branch rules back.
Do not create a second queue ruleset or replace `Protect` with the manifest.
See [the scheduling change](../../Changes/Ci/QueueRuntimeScheduling.md).
