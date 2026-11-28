# Plain drawing note held-out method

PR #121 adds a metadata-only pre-unseal method for the two previously locked ordinary plain-note sources. The [method](../../../../../../re/solidworks/records/DrawingPlainNoteHeldoutMethod2026.md) specifies thirteen fresh native roles, independent source/candidate text and position editing, immutable saves and reopen, actual tree comparison, typed owner/alias checks, and explicit source/presentation/rendering admission boundaries.

The [standalone verifier](../../../../../../re/tooling/sw2026/drawing_notes/VerifyPlainNoteMethod01.py) checks only the public lock hashes and frozen method. It has no SDK or CAD runtime import and cannot release sources or qualify a writer. Use its required method/hash/source-lock/output arguments with an unused output. Its syntax was checked; execution is left to root.

The [preparation receipt](../../../../../../re/solidworks/measurements/2026/DrawingPlainNoteMethodPreparation01.json) binds the already passed six-process disclosed native result and retains the complete SDK/writer/evaluator freeze as pending. No private payload was read, no native process or local test was run by this lane, and no public behavior or qualification flag changes.
