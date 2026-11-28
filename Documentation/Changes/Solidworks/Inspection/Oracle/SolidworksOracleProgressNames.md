# Explicit oracle progress filenames

The macOS host supervisor accepts repeatable `--progress-file BASENAME` options. Supply the exact JSON filenames used by the batch's checkpoints. The observer scans those names under the new progress root, including nested folders. Omitting the option selects `Record.json`. The host report lists the selected names and records only content changes.

Six isolated process checks exercise the default, `Inspection.json`, both names together, an unlisted writer, an unchanged writer and a rejected path argument. Only changing selected files postpone the no-progress deadline. Both timeout fixtures confirm termination of their owned host transport. [Process receipt](../../../../../re/solidworks/measurements/2026/OracleProgressBasenames01.json)

For the ordinary revolve oracle, use `--progress-file Inspection.json` and the normal complete native record for the final measurement. [Transport observation](../../../../Gotchas/Conversion/Solidworks/Tracing/OracleWatchdogNeedsActualProgressNames.md)
