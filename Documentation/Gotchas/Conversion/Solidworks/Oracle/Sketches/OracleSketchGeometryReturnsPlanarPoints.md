# The sketch geometry observer returns planar coordinates

`AuthorCurves.geometry` returns two local coordinates for each sketch point. The neutral rectangle predictor carries three coordinates. Comparing the raw tuples with strict zip stops the comparison after the two matching coordinates.

For a qualified local XY rectangle, verify the predicted Z coordinate and then compare the two retained coordinates and every ordered endpoint. The corrected comparison preserves the generated inputs and passes both native cases. [Native receipt](../../../../../../re/solidworks/measurements/2026/NamedBodyColdReuseNative01.json)
