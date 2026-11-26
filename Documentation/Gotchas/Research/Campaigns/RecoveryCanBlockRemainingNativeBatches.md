# Recovery can block remaining native batches

## Expectation

A recovered native application can appear ready to execute every remaining batch.
Counting controller attempts can appear to measure unique corpus coverage.

## Observed behavior

The [feature ladder campaign](../../../../re/FeatureLadders2026/README.md) lost its SOLIDWORKS COM RPC connection.
Supported recovery allowed three additional successful batches before the same connection failure recurred.
The service rejected subsequent dispatch while its recovery marker remained set.
An earlier failed attempt remained parked after a later successful retry of the same logical case.

## Workaround

Keep the original failure and retry receipts. Aggregate results by the original logical case identity.
Distinguish native failures from dispatch-blocked cases and strict reader refusals.
Inspect host process and service evidence before further native recovery.
Continue independent offline and Fusion work. Do not repeatedly recover or resubmit successful batches.
This observation does not establish the root cause of native process loss.
