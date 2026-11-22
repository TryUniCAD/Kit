# Thin-revolve display coordinates use a multiplication

The strict thin-revolve projection exposes typed metre coordinates and wall
lengths in millimetres using multiplication by 1000. Division by 0.001 can
produce an adjacent binary64 value. Treating either calculation as the same
conversion caused the disclosed Right Plane readback to fail its exact
coordinate check.

Compare the public value with the calculation that projected it. Recover the
neutral millimetre input by requiring the existing exact inverse to reproduce
the typed metre value. The measured writer still requires complete byte and
whole-document equality before publication.

[Measured thin-revolve evidence](../../../../re/solidworks/records/MeasuredThinRevolve2026.md)
