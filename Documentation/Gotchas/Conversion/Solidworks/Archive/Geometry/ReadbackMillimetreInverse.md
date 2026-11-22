# Displayed millimetres may change a native metre word

The strict line-boss reader preserves the binary64 metre coordinates in the
typed point rows and the depth in the actual D1 driver. It also exposes those
values in millimetres. Multiplying a displayed value by `0.001` can produce
an adjacent metre value. The measured Skew depth displays
`12.750000000000002 mm` and owns the metre value `0.012750000000000001`.

Verify the displayed value by the original metre-to-millimetre multiplication.
Use a representable millimetre input whose forward write conversion recovers
the exact metre word. The writer verifies the complete regenerated readback as
well as the native-measured payload. [Measured part evidence](../../../../../../re/solidworks/records/MeasuredPartPublication2026.md)
