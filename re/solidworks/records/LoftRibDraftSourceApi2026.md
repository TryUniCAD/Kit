# Installed SOLIDWORKS 2026 loft, rib and draft source interfaces

The Windows 11 Parallels guest registered release 34.0 of both SOLIDWORKS
type libraries. The capture verified the installed SP05.2 executable
`34.5.2.0604` and its SHA-256 through the versioned COM registration before
loading either library. An independent expanded capture agrees on every
retained method and enum. The query created no SOLIDWORKS process, authored
no native file, and accessed no held-out source. [Installed API receipt](../measurements/2026/LoftRibDraftInstalledApi01.json)

| Source feature | Installed creation interface | Source ownership to observe |
| --- | --- | --- |
| Loft | `IFeatureManager.InsertProtrusionBlend2`, dispatch member 186 with 18 arguments | `ILoftFeatureData` exposes the ordered profiles, profile count, pick points, guide curves and tangency. A signed parallel-plane contrast can vary each circle's diameter and the datum distance independently. |
| Rib | `IFeatureManager.InsertRib`, dispatch member 162 with ten arguments and no feature return | `IRibFeatureData2` exposes its supporting body, sketch reference index, symmetric thickness, extrusion direction and side. A one-line source still needs to bind the actual reference index and the inward material direction. |
| Draft | `IFeatureManager.InsertMultiFaceDraft`, dispatch member 54 with six arguments | `IDraftFeatureData2` exposes its angle, directed pull, neutral plane, drafted faces and propagation. Select the actual neutral cap and target face with marks 1 and 2 for the isolated-face trial. |

The capture also binds the actual selection-point getter and setter, selection
mark access and the entity selection calls. The signatures establish available
source authoring calls. Ordering, sketch connector alignment and signed
effects require native measurement. [Loft source operations](https://help.solidworks.com/2026/english/SolidWorks/sldworks/t_creating_lofts.htm) [Rib arguments](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~InsertRib.html) [Draft arguments and marks](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~InsertMultiFaceDraft.html)

The regenerated SP05.2 serializer inventory independently lists
`moBlend_c` in `sldmodu.dll` at `0x4cad6890`, `moRib_c` in the same module at
`0x4c3aba60`, and `moDraft_c` in `sldmopartu.dll` at `0x1802daa40`. Their
reached archive fields and model-only construction rules remain open.
[Serialize map](../../data/Serialization/SerializeMap2026.json)

Run the [capture](../../tooling/sw2026/ReadLoftRibDraftApi.py) with the
registered Windows Python 3.12 in the current user session of the
`Windows 11` VM. From macOS use `prlctl exec "Windows 11" --current-user`,
the absolute guest script path and `--output` with a new guest file.
The measured receipt SHA-256 is
`0e9eb0e2d5020e2c78523e65f22e3d21d441fbc69b95a09661c153b5bf0cda97`.
