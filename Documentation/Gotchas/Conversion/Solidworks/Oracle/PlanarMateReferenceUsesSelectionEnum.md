# Mate reference type uses the selection enum

`IMateEntity2.ReferenceType2` reports `swSelectType_e`. All three measured principal plane mates returned `swSelDATUMPLANES` (4). Their eight parameters describe the placed plane point and normal.

Use the selection enum for this property. Keep the archived mate geometry type in its own enum. Applying plane geometry type 3 to the COM property rejected the three valid observations before saving. [Native observation](../../../../../re/solidworks/measurements/2026/PlanarMateReferenceType01.json), [reference type API](https://help.solidworks.com/2025/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IMateEntity2~ReferenceType2.html), [SOLIDWORKS 2026 selection enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSelectType_e.html?id=2.10.1.729)
