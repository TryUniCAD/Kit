# Read implicit SOLIDWORKS cylinder body labels

The normal SOLIDWORKS 2026 part reader retains the actual implicit label on the ordinary saved single-cylinder profile. It binds the selected active partition, the sole real archive atom, its producing extrusion and the full decoded solid before setting `DesignBody.name` and `BrepBody.design_body_id`. Inspect `metadata["solidworks.native_body_names"]` for that proof.

For the existing strict cache-free Front diameter and reversed Top radius profiles, the label follows the actual feature that produced the computed neutral solid. That path retains only the source feature provenance and the existing reconstruction diagnostic. Metadata-only reads keep their previous body view. Explicit-name branches retain their own checks.

Ninety guarded SDK processes passed 216 paired comparisons, including the disclosed D01 and native-saved radial children, both cache-free cylinder modes, three explicit-name controls and 32 rejection or fallback cases. The public calls opened only their declared linked child files. The reader change adds no native write or held-out coverage.

[Source ownership and verification](../../../../../re/solidworks/records/ImplicitCylinderBodyNames2026.md)
