# Native boss display precision is not driving precision

## Expectation

A displayed depth can appear to preserve the native driving value.

## Observed behavior

On revision `c4e8a34186bdd173dad37d843b79bc8a3a59ebb9`, the Discovery01 API records 13.371 mm and 21.463 mm depths.
The SDK driver and extrusion length contain 13.37 mm and 21.46 mm.
The retained native-value attribute contains the same rounded projection.
The four older two-decimal Author04 controls do not expose this precision loss.

## Workaround

Compare the typed driver and feature length against the independent API value.
Keep the input unqualified when those values differ beyond the stated tolerance.
Do not recover missing precision by formatting display text or fitting known controls.
Use the separately evidenced native parameter grammar before qualifying a reader change.

See the [recorded precision comparisons](../../../../re/solidworks/NativeBossProof/Evidence/DiscoveryDepthContrast.json).
