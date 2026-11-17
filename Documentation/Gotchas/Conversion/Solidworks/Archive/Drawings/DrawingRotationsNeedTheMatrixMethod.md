# Drawing rotations need the matrix method

The original compact SDK drawing grammar reached only views with the implicit identity rotation. On the first rotated source it reached `mgMatrix_c.restore` and failed because the method was absent from the exported SDK table.

Include the measured nine-double method when inspecting rotated views. SOLIDWORKS applies a point using the columns of its saved basis, then uniform scale and translation. Use those columns as the rows of the SDK's matrix. An identity view gives the same result in either order, so check rotated model points as well as names and coefficients. The four scaled-source comparisons verify this through the public reader. [Source rule and receipt](../../../../../../re/solidworks/records/DrawingScaledViewProjection2026.md)
