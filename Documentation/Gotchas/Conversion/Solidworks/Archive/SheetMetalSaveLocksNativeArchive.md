# Save sheet-metal discovery copies before hashing

In the native SP04.1 run at revision c6c80926, SaveAs published an unqualified sheet-metal part but kept it open as the active document. The capture's readback failed with Windows sharing violation 32 while the archive was still open. The file became available for offline hashing after the owned process exited. Both stock controls passed. The archive remains unqualified because the native part failed its authored geometry check.

Use the native Save as copy and continue option when preserving successive states of one owned document. Verify that the original authoring document stays active and bind the closed copy to its exact digest. A fresh process independently reopens each accepted save. [Native save options](https://help.solidworks.com/2025/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSaveAsOptions_e.html) · [Capture procedure](../../../../../re/solidworks/records/SheetMetalCapture2026.md)
