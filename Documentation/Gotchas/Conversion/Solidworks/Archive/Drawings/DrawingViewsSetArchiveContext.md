# Drawing views set an archive condition for nested geometry

In SOLIDWORKS 2026 a sheet and an ordinary drawing model view can both contain `moRefPlane_c`. The nested plane under a model view lacks the four-byte `moAtomFeature_c` `f3d0` presence word. Reading both planes with the same archive condition places the cursor four bytes into the next typed class tag in the view.

Set condition `0x40` for the affected `moDrView` archive fields and restore the enclosing condition before continuing. The pinned `sldmodu.dll` sets the bit at `0x4c958f87` and restores it at `0x4c95cb24`. The typed Definition process uses the same context bracket for decoding and re-encoding. [Drawing Definition grammar](../../../../../../re/solidworks/records/DrawingDefinitionGrammar2026.md), [Exact stream measurements](../../../../../../re/solidworks/measurements/2026/DrawingDefinitionCheck01.json)
