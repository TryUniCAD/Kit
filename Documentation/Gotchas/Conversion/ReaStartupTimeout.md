# REA startup timeout on large DLLs

## Expectation

The REA Ghidra provider should complete ordinary startup analysis within its default deadline.

## Actual behavior

The 2026 `sldmodu.dll` can exceed the 330,000 ms `REA_GHIDRA_STARTUP_TIMEOUT_MS` limit while making valid progress.
The resulting error is `provider_timeout`, with an incomplete import and `failure_kind=timeout`; it is not format corruption.

## Workaround

Inspect `message`, `remediation`, `details`, and the retained standard output before changing target binaries or disabling analyzers.
For this workload, set `REA_GHIDRA_STARTUP_TIMEOUT_MS=3600000` and reuse the same tool installation.
The full run completed with REA evidence `ev_68ff5b10754cc221cc281307f887ece271735c7ff16bc2249d674a0117761ab3`: 93,329 procedures and 64,252 strings.
See [the runtime format closure](../Changes/Solidworks/SolidworksFiveLineNativeHistories.md).
