# Guest-private blank drawing source slots

PR #121 adds a source-only protocol for two independent ordinary blank ANSI A drawing intents. Sheet names and initial/edit scale ratios are created and sealed only in guest-local private storage. Root's serial recipe authors each native drawing, edits the real sheet scale, saves a distinct derivative, reopens it in a fresh process and takes pristine controls before publishing a hash-only lock.

The tool reuses the existing native drawing author, sheet/tree observations and cache inspector. The inspector accepts an optional edit ratio while preserving its previous 3:2 default. Preparation requires a new external packet, the exact disclosed drawing control, explicit guest Python and private guest-local output. No concrete blind values or native payloads are created on the host.

Two host verifies pass. Changed packet/tool/control identities and host sealing refuse. Three scoped Python files pass AST/compile; no native execution ran at this freeze. Existing internal blank construction predates the new source cohort. The protocol reserves these cases for a later frozen public-writer equivalence method and enables no public writer or held-out acceptance.

See the [source protocol](../../../../../../re/solidworks/records/BlankDrawingPrewriterProtocol2026.md), [SDK blank construction](../../../../../../re/solidworks/records/SdkBlankDrawingFile2026.md) and [existing disclosed native proof](../../../../../../re/solidworks/records/SdkBlankDrawingNative2026.md) for ownership, commands, full comparison gates and remaining limitations.

Both native source slots passed the complete ten-process run on SOLIDWORKS 2026 SP05.2 with four pristine controls. The public receipt publishes only source, intent and edited hashes. [Native source lock](../../../../../../re/solidworks/measurements/2026/BlankDrawingBlindSourceLock01.json)
