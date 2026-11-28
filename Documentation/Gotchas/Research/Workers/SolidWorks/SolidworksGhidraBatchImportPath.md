# Windows Ghidra batch import can reject the installed loader path

The Ghidra 12.1.2 headless batch launcher rejected the exact installed SOLIDWORKS loader path with a command parser error. The same bytes imported from a local path without spaces and parentheses.

Use an isolated local directory outside the repository for the optional import copy and analysis project. Verify the copied executable's full SHA-256 before importing it. Keep the loader and any decompiled listing in that local directory. For a known function address, `-noanalysis` with a focused script avoids waiting for unrelated whole-program analysis.

[SP04.1 loader evidence](../../../../../re/solidworks/records/VendorBlindBossSourceAdmission.md#loader-trace-and-reproducibility)
