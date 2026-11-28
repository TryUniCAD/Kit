# SOLIDWORKS sheet-metal native capture recipe

The research launcher authors the six populated sheet-metal contrasts on SOLIDWORKS build 34.4.1.1011 through the existing owned-process capture host. It saves and reopens each contrast, including the separate length edit and restoration, and requires a receipt-pinned stock control before and after the batch. It records the authored arguments, feature and body observations, archive hashes and process receipts. It isolates the held-out archive and its receipt under a separate seal. A geometry failure may emit a separately labeled diagnostic archive for a valid discovery body. That archive is unqualified and the run still fails.

Use the PowerShell command and stock receipt requirements in the [capture procedure](../../../../../re/solidworks/records/SheetMetalCapture2026.md). The [launcher](../../../../../re/automation/PairedCaptures/SheetMetal/RunSheetMetalCapture.ps1) also has a compile-only path that checks source and installed cohort pins without opening SOLIDWORKS.

The binding was compiled against the installed SOLIDWORKS 34.4.1.1011 interop. The populated capture, native API authoring behavior and save/reopen results require an oracle run. The recipe supports a research comparison and provides no populated reader or writer acceptance on its own.
