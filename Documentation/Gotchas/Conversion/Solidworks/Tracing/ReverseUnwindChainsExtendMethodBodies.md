# Reverse unwind chains can extend a method beyond its entry record

A matching x64 PE runtime-function entry does not necessarily describe the whole native method, even when that entry has no chain flag. Other runtime-function entries can chain back to it.

In the pinned SOLIDWORKS 2026 UI image, `uiModelDoc_c::iGetViewArray` begins at `0x49797990`. Its first runtime-function record ends at `0x497979b6`, only 38 bytes later. Two later entries chain back to that first record and extend the declared ownership to `0x49797b11`, for 385 bytes in total. The initial conditional branches already target those later fragments. Inspecting only the first record would miss the actual splitter-restoration call.

Resolve each chained unwind record to its ancestor and collect every reverse child in the complete exception table. Retain the individual half-open ranges, their hashes and whether they are contiguous. Declared unwind ownership does not establish ownership of unrelated tail callees. The [caller receipt](../../../../../re/solidworks/measurements/2026/ViewLoaderCallers01.json) records all three fragments; the [change entry](../../../../Changes/Solidworks/Inspection/Presentation/SolidworksInitialViewLoaderTrace.md) describes the separate restoration paths. Vendor instructions and decompiled listings remain external.
