# Box stock uses its actual placement

A FreeCAD `Part::Box` may be independent of other features and still carry a translation. The disclosed FreeCAD 1.1.4 standalone primitive has placement `(4.25, 6.125, -2.25)` mm. A distinct legacy document contains an origin box and another box translated by 181.8 mm. That second box's literal label ends in `006` while its stored height is 5 mm.

Select the actual `Part::Box` and its own `Shape` property, then read its typed dimensions and placement. The origin-stock preparer refuses translated or attached shapes. Carry translation forward as authored geometry when a separately proven native model supports it. [Disclosed source and placement proof](../../../../../re/solidworks/records/SdkFreecadPrimitiveStock2026.md)
