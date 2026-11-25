# The untitled Fusion root component name is read-only

## Expectation

A native capture script can use the general component name setter on the root of a fresh untitled design.

## Actual behavior

Fusion 2706.1.17 raised runtime error 3 at that setter before it authored the auxiliary cuboid. The task-owned process closed with zero open documents. Autodesk describes the general component setter and identifies the root component name with the file name. [Component name API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Component_name.htm) · [Fusion document and root names](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/OpeningFilesFromWebPage_UM.htm)

## Workaround

Leave the root name assigned by Fusion. Record the capture identity in its request and archive name. The geometry probe can assign sketch and feature names independently. The [capture guide](../../../../../re/Fusion/LocalOracle/SavedCuboidRoundTrip/README.md) records how to prepare the requests.
