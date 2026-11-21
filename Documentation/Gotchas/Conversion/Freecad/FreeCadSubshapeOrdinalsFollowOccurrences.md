# FreeCAD subshape ordinals follow stored occurrences

The exact F14a Body and primitive shapes each store 34 OCCT records. Their physical `TShapes` references and the SDK's placed B-rep suffixes differ from the one-based names used by FreeCAD's `TopExp::MapShapes` lookup. Sorting shape records or SDK entities by their IDs can therefore change which face, edge or vertex a source pointer names. [FreeCAD indexed cache](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/Part/App/TopoShapeCache.cpp#L163-L179) · [OCCT indexed traversal](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_1/src/TopExp/TopExp.cxx#L30-L40)

For the qualified box comparison, follow stored child occurrence order, verify each repeated raw shape shares one location path, and resolve its actual placed role. Check the Body's element-map offset and its actual child XML tag before binding a named primitive entity. [Lineage receipt](../../../../re/solidworks/measurements/2026/SdkFreecadF14aTopologyLineage01.json)
