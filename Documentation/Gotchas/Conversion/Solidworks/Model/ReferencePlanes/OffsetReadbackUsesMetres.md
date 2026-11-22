# Offset readback keeps the native metre drivers

The strict offset reader projects the datum pose and circle radius in
millimetres. The constructor scales a millimetre pose by `0.001`. For the
measured reversed Top part, multiplying the native datum origin by
`1000.0` for display and then multiplying by `0.001` for construction changes
the original binary64 word. The reader also exposes the radius with its
own display conversion.

Check the projected pose, fixed centre and each displayed driver against
the actual typed source owners. Use the signed native metre distance, the
exact native radius and boss depth, and divide the metre datum origin by
`0.001` for the constructor's millimetre pose validation. The native archive
pose comes from the exact signed metre distance. Keep the original document
for the full readback comparison. [Disclosed offset proof](../../../../../../re/solidworks/measurements/2026/SdkOffsetColdReadback01.json)
