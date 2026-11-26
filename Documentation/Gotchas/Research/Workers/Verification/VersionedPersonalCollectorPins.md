# Personal native verification requires exact collector pins

## Expectation

A reachable personal CAD API appears ready to verify a newly installed Kit revision.

## Observed behavior

The API rejected this checkout with HTTP 409 because its exact collector revision was absent.
The installed default collectors remained valid for their earlier revision.
The source reader and native measurements must use the same collector bytes.

## Workaround

Register the exact Git-verified collector set in the service's existing versioned collector store.
Keep the default collectors unchanged.
Verify every file hash before dispatch.
Do not substitute hashes or remove revision checks.

This campaign registered ten files from `2b7497e9e117781043bdac8a2c50354ecad30d82`.
The canonical collector revision is `e04bf545290a253193c72d210719d1c0eebb4c5464b0a550daf59fd511c58bd1`.
Subsequent built-in verification measured healthy controls and retained semantic failures.
See the [campaign evidence](../../../../../re/CutsRevolutions2026/README.md).
