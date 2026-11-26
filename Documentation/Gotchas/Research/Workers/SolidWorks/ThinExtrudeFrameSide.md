# SOLIDWORKS thin-wall side follows the native sketch frame

The same one-sided thin-extrude mode can land on opposite sides in two recipe
bases. On SOLIDWORKS 34.4.1.1011, mode 0 extended the directed profile into
negative local V in XY and YZ. In XZ the actual sketch normal was opposite the
recipe normal, and mode 0 extended into positive local V. Reversing the axial
extrusion kept the same wall side. The midplane mode extended equally in both
directions.

For these catalogue line profiles, choose one-sided mode 1 when the native
and recipe sketch normals agree, and mode 0 when they oppose. Use the
independently predicted body bounds and centroid to verify the result after
saving and reopening.
[Capture evidence](../../../../Changes/Research/Supervisor/Catalogue/SolidWorksThinWallSide.md)
[SOLIDWORKS thin-wall enumeration](https://help.solidworks.com/2026/english/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swThinWallType_e.html)
