# Retry temporary errors when downloading sealed fixtures

When a Git batch fetch cannot supply a historical blob, capture-history setup downloads it from the pinned GitHub revision.
The fallback retries HTTP 502, 503, and 504 with one-second and two-second delays, for up to three requests per blob.
Each attempt uses the same repository, revision, and path. The file-size limit and Git blob identity check still apply before storage.

[Windows CLI shard 3](https://github.com/TryUniCAD/Kit/actions/runs/45243315638/job/137933735653) received HTTP 503 before the tests started on PR #277's `b7de0ad4` merge candidate.
The [CI aggregate](https://github.com/TryUniCAD/Kit/actions/runs/45243315635/job/137933440869) reported the shard failure. The [merge queue run](https://github.com/TryUniCAD/Kit/actions/runs/45243315484) was cancelled.

The shared test plan collects process cases that use a real HTTP server and a disposable Git repository.
They cover recovery after HTTP 503, retry exhaustion, HTTP 404, and rejection of incorrect content after a retry.
Hosted verification on this revision is pending.

See [the setup failure and recovery](../../Gotchas/Ci/Windows/SealedFixtureHttpFailures.md).
