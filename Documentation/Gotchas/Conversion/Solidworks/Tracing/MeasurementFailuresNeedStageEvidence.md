# Attribute native failures to recorded stages

## Expectation

A report with a COM exception and no `opened` field proves that native open failed.

## Observed behavior

The old measurement helpers returned their records after rebuild, property queries, and document cleanup.
An exception in a later step discarded the earlier open result.
The selected body-collection continuation was also identified as part destruction, which can occur during several failure paths.
Neither observation identified the failed public API call by itself.

## Workaround

Retain the partial record before each native call.
Record separate start and return markers for open, rebuild, queries, and close.
Preserve the original failing stage when cleanup executes.
Keep process termination codes separate from COM exceptions.
Treat historical aggregate reports as failed measurements when their exact failing stage is unavailable.

The [stage report change](../../../../Changes/Solidworks/SolidworksOracleStageReports.md) describes the corrected entry points.
