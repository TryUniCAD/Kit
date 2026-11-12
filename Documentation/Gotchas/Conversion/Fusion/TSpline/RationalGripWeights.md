# Native vertex edits can perturb TSM grip weights

A box and initial plane use weight 1 in every `0g` record. A native plane vertex edit produces one weight `1.0000000000000002`. Requiring exact unity rejects a valid native output; rounding it away loses a persisted value.

The native `Grip_point3d` export returns all four doubles from the 32-byte grip record. Native validation reads the fourth double, compares it with zero and reports an invalid grip weight when it is not positive. Preserve finite positive weights exactly and reject nonfinite or nonpositive weights. The typed writer emits enough decimal precision to round-trip the value without normalization.

[Native field evidence](../../../../../re/Fusion/Reconstruction/TSpline/FieldEvidence.json) and [the edited source](../../../../../re/Fusion/LocalOracle/TSpline/PlaneEdited.tsm) bind this case.
