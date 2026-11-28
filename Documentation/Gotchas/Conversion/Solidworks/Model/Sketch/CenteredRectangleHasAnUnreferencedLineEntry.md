# Centered rectangle has an unreferenced line entry

The native centered rectangle's archived line array contains an auxiliary line from its center to a corner. The native sketch API returns six segments, and its center relations select only the two actual construction diagonals and the Origin reference. Using all seven archived lines as body edges would change the contour.

Build the four body edges and the two construction diagonals from the authored geometry. The measured generated model keeps full constraints through both edits and fresh reopen. Both vendor-saved edits retain six archived lines. [Measured result](../../../../../../re/solidworks/measurements/2026/GeneratedCenteredRectangleNative01.json)
