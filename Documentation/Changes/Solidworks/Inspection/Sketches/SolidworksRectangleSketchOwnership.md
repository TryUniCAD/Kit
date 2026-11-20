# SOLIDWORKS rectangle sketch ownership

The SDK now reads a dimensioned four-line SOLIDWORKS 2026 rectangle as one closed profile and returns its two linear driving relations and correct body summary bounds. The reader verifies the point and line array layout and the empty arc count for this ordinary principal-plane sketch. Other layouts continue through their existing profile readers. [Typed ownership and native witnesses](../../../../../re/solidworks/records/RectangleSketchOwners2026.md).

The integration checks open the disclosed A13 child, a 2026 annulus, a legacy mixed circle and rectangle sketch, and three independently generated assembly pairs. The generated pairs use the opt-in research partition probe for the default B-rep read. This change affects SDK inspection. [Public reader checks](../../../../../tests/Convert/Solidworks/Core/Readers/SolidworksRectangleReaderTests.py).
