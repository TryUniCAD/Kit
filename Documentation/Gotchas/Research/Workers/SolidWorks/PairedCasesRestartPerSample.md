# Paired cases restart SOLIDWORKS per sample

## Expectation

Increasing `--workers` can appear to increase native catalogue parallelism or share application startup across every recipe.

## Observed behavior

The earlier submission path scheduled P01–P05 as separate capture jobs.
Each job launched one process for authoring and another for independent reopening.
Only written-recipe programs used the existing three-case batch runner.
The native pool and application resource each had capacity one.

The local run `Discovery-20261124-201831` demonstrated this distinction.
All first 16 completed decoder jobs overlapped native capture.
Successful capture attempts averaged 103.51 seconds, while decoder jobs averaged 5.91 seconds.
Increasing the decoder ceiling did not change the native job boundaries.

## Workaround

New plans automatically batch paired and written cases through the same native runner.
Each batch uses one authoring process and a separate verification process.
Existing saved plans preserve their job definitions.
Use a fresh run directory and the new source revision to obtain automatic batching.
The [change entry](../../../../Changes/Research/Supervisor/Catalogue/PairedCaseBatching.md) records implementation and verification status.
