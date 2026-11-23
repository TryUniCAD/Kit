# A chamfer angle edit can change the exterior text station

The transverse signed chamfer keeps essentially the same local D2 text
point and clearance in its original and edited native saves. The live
angle edit rotates the first witness across that point. SOLIDWORKS
changes the stored text station from `1.5` to `-0.5`.

Keep the text point separate from the driver. Compute the station in the
actual annotation basis from the two ordered inward rays. The ordinary
acute branch checks the first exterior test before the second.
An unqualified interior or near-boundary point requires a separate rule.

[Exact build and paired source evidence](../../../../../../re/solidworks/records/ChamferSavedDisplays2026.md)
