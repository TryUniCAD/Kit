# Saved chamfer stock lines can use either storage direction

A saved rectangular profile can store its lines in individually reversed
directions. Its line order identifies the connected sequence and the
permanent line IDs identify the side faces. Taking the raw start of each
ordered segment can yield duplicate vertices and fail an otherwise ordinary
rectangular stock check.

Read the connected ring through the shared prism contour reader. Keep the
actual permanent line IDs for face selection and compare the resulting
point order with the corresponding saved stock. The disclosed originals
and depth-preserving chamfer edits store four active segments, four active
axis relations and one cached region. [Warm read proof](../../../../../../re/solidworks/records/ChamferDistancePairSavedRead2026.md)
