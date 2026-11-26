# Revolution angle ownership and extrusion controls

The file-driven SOLIDWORKS audit now checks competing revolution angles against the owning feature record. It follows the saved axis reference and end specification, reads the angle in radians, compares the two redundant angle fields byte for byte, and checks the public parameter’s value, unit and provenance. Each offset must fall within the feature’s span.

For the turbine wheel, the three 360° revolution angles reside at offsets 69920, 139614 and 178319. All three refer to axis 46. The evidence identifies the angle for each feature even though the displayed values coincide. The layout comes from the [revolution field map](../../../../re/solidworks/features/Revolve.md).

Extrusion discovery now searches the bounded collection of tracked control parts used by the other field experiments. It learned a depth layout from independent streams and different depth values, then verified the wheel’s 2.54 mm cut at offset 158970 against its copy at 159553.

Run `kit run solidworks --input <part.SLDPRT> --directory <new-directory>` and inspect `Input-dimension-evidence.json`. These findings concern saved parameters. One circular-pattern dimension in this file still lacks sufficient independent evidence.
