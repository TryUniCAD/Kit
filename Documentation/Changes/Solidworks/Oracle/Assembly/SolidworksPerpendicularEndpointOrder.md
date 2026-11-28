# Preserve native perpendicular endpoint order during source measurement

The source observer now matches each returned mate endpoint to its authored
occurrence and principal plane. It verifies the occurrence and datum IDs
and the model-space point and normal. It retains the order reported by
SOLIDWORKS for its save and reopen checks.

The D02 probe selected the Right Plane before the Top Plane.
SOLIDWORKS returned the Top Plane first. Both controls passed, and the
first returned endpoint matched the predicted occurrence and plane.

[Measured order and source protocol](../../../../../re/solidworks/records/PerpendicularMateSourcePosition2026.md)
