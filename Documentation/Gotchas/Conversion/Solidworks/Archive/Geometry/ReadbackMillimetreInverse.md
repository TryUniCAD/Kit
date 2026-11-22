# Displayed millimetres may change a native metre word

The strict line-boss reader preserves the binary64 metre coordinates in the
typed point rows and the depth in the actual D1 driver. It also exposes those
values in millimetres. The measured Skew depth owns
`0.012750000000000001 m`. Multiplying that word by 1000 produces
`12.750000000000002 mm`. Dividing by the actual forward coefficient
`0.001` recovers the authored `12.75 mm`.

Verify the displayed value with the same forward coefficient.
Use a representable millimetre input whose forward write conversion recovers
the exact metre word. The writer verifies the complete regenerated readback as
well as the native-measured payload. [Measured part evidence](../../../../../../re/solidworks/records/MeasuredPartPublication2026.md)
