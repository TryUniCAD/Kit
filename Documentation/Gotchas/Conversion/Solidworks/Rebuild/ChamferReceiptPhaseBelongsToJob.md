# Chamfer receipt phase belongs to the job

The per-phase summary in the chamfer source lock exposes a top-level `phase` field. The detailed `Record.json` produced by `AuthorCurves.Recorder` keeps the phase and authored case in `job`. The first sealed evaluation used the summary shape for the detailed receipt. Both controls passed, but validation stopped at the first source receipt.

Validate each summary and detailed receipt according to its own schema. Check `job.phase` and `job.case` against the locked slot, and run custody verification before opening the source in SOLIDWORKS. [Failed run and retry protocol](../../../../../re/solidworks/records/ChamferColdHeldoutProtocol2026.md)
