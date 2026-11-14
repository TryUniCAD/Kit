# Triangle marker coordinate precision

## Expectation

Native marker coordinates reconstructed in millimetres are suitable for reconstructing the native writer's floating-point fields. Neutral presentation and native serialization therefore appear to consume the same values without loss.

## Actual behavior

The neutral marker decoder rounds millimetre coordinates to 12 decimal places. Passing that normalized value back into the writer loses additional source precision, and a tolerance-based completion proof can still accept the result. Multiplying a stored native metre value by 1000 and then dividing again is also an unnecessary floating-point round trip.

## Workaround

For the bounded three-line writer, recover the original `coordinates_metres` pairs from the same validated point markers and pass them directly to the six native coordinate fields. Require their normalized millimetre values to equal the already validated polyline before writing; otherwise reject the source.

Neutral readers can retain their documented display normalization. Native serialization must not treat that normalization as the source of truth. Public-writer integration coverage compares all six emitted doubles against `source_mm / 1000` for coordinates with more than 12 decimal places.

For a native reader, `NativeProfile.coordinates` remains the normalized presentation value while `NativeProfile.native_coordinates_mm` retains the measured metre pairs converted to millimetres without 12-decimal rounding. `MapPolyline` uses the latter when present. The metre-pair consistency checks must apply `Clean(round(value * 1000, 12))` on both sides: using `round` alone rejects valid near-origin values that `Clean` intentionally maps from 1e-12 mm to zero.

This doesn't promise a compatible freecad interpretation for every native-derived neutral document. That requires its own history and parameter binding acceptance rather than coordinate recovery alone.

See [the triangle writer](../../../../src/convert/adapters/solidworks/programs/resolved/polyline/threepoint/Program.py), [the precision regression](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
