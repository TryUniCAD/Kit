# Resolve the edge-flange length on its native sketch feature

In the SP04.1 A-edge discovery, profile creation and native flange insertion completed. The capture stopped before saving because its document-level dimension lookup used a synthesized name and could not establish the requested length on the inserted flange.

Name the driving profile dimension before inserting the feature. After insertion, resolve that exact name through native sketch subfeatures owned by the flange. Require a single driving dimension and record the full names and measured length both before and after insertion and when reopening. Use the same native dimension for the edit and restoration. [Feature parameter API](https://help.solidworks.com/2021/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature~Parameter.html) · [Capture procedure](../../../../../re/solidworks/records/SheetMetalCapture2026.md)
