# External file reference flags normalize on load

The generated SOLIDWORKS drawing's self-reference flag byte `f58` is `0`. The disclosed reduced native drawing stores `8`. In archive version 19000, their different wire bit 3 yields the same flags immediately after the native load operation.

`sldarchiveu.dll` reads the byte at `0x319fdcfb–0x319fdd09`. The version branch at `0x319fdd74` reaches `0x319fde32`, which sets runtime bit 8, then clears bits 3 and 1 at `0x319fde47–0x319fde51`. The save path computes wire bit 3 from runtime bit 8 at `0x319fd9b8–0x319fd9cd`. Compare native save behavior at the actual runtime owner when a self-reference differs only in this flag. [Save-path evidence](../../../../../../re/solidworks/records/DrawingContainerSaveFraming2026.md#shared-save-return-edges)
