# In-memory strict readback reads packaged grammar

Reading generated archive bytes in memory can still read a packaged format grammar from disk.
The SOLIDWORKS public strict reader calls `LoadPartLayouts`, which reads `Config/RootLayout.json` through `pkgutil.get_data` on each call.
An audit that denies every file open therefore rejects this reader even when it receives no native source path.

Keep generation and readback phases separate.
Deny every file read during generation.
For readback, permit only the exact declared grammar resource in read mode and bind its content hash.
Report that resource read separately from model-input reads.
Do not allow arbitrary files or native archives as a workaround.

[Fresh-process evidence](../../../../re/solidworks/WriterResearch/Evidence/TopCompositionBoundary.json) records one named JSON read, one hash-bound grammar read and no other external access.
