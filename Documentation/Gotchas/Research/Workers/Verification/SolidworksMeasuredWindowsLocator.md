# Windows staging changes the measured locator

## Expectation

A public writer check can use a temporary host file and an explicit measured Windows locator.
Each malformed receipt should then reach its expected lifecycle validation.

## Observed behavior

`WritePathStaged` replaces `final_destination` with the resolved destination path.
On Windows, the temporary host path therefore changes the archive's encoded locator and complete digest.
`CheckMeasuredPartWriter.run_refusals` can reject a malformed reopen receipt at the earlier exact-digest gate.
The observed diagnostic was `regenerated SOLIDWORKS part has no unique exact native measurement`.

This rejection preserves the publication boundary.
It does not prove that the requested reopen validation ran.

## Workaround

Use empty binary streams with the exact measured `final_destination` for receipt lifecycle checks.
Use deliberately populated streams to verify that refused writes preserve bytes and cursor position.
For file publication checks, create the file at its actual measured locator.

The [publication process check](../../../../../re/solidworks/EncoderBoundary/CheckPublication.py) uses the stream path.
The existing [CLI helper](../../../../../tests/Convert/Solidworks/PlainWriting/LeaseMeasPath.py) handles measured file locations.
