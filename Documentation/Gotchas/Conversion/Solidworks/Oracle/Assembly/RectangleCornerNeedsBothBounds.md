# Match both bounds to identify the lower-left sketch point

Two points on the same vertical edge can differ in their X values by
floating-point rounding. Ordering the points by X then Y can select
the upper point before considering Y. In the native D02 trial this
shifted the rectangle one full height.

Compute the minimum X and Y independently. Bind the unique point
matching both with the geometric tolerance before setting its
coordinates. The corrected native readback verifies all four corners.

[Measured original and corrected point positions](../../../../../../re/solidworks/measurements/2026/PerpendicularMateSourcePosition04.json)
