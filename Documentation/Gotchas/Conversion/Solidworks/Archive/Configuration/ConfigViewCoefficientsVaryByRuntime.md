# Standard-view near-zero coefficients can vary across runtimes

The same frozen SOLIDWORKS 2026 offset-plane writer and disclosed neutral
request produced different physical file hashes on macOS and Windows. Both
individual runtimes built their candidate deterministically. All ten logical
streams had the same sizes. Nine streams matched exactly. The remaining
`Contents/Config-0` stream differed at eight near-zero binary64 view matrix
coefficients inside the ordinary part's four standard views.

The linked typed maps and fields located the differences. The two runtimes
represented those entries as `-3.552713678800501e-15` and
`-3.5527136788005e-15`. The Windows-built candidate passed the disclosed native
comparison with all 26 native feature rows, the driving distance edit, a clean
save and fresh reopen. All four processes including both controls passed.
The [receipt](../../../../../../re/solidworks/measurements/2026/ReferencePlaneOriginalHeldouts01.json)
binds the typed difference and the native comparison.

Pin the generating runtime when comparing byte hashes. For a portability gate,
compare typed structure and measure the portable behavior on the exact target
application. Retain the computed coefficients when both forms are qualified.
