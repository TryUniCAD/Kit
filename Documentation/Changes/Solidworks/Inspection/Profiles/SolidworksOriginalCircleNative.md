# Verify two original native SOLIDWORKS circle parts

Two pre-writer locked originals match independently generated SDK parts
through native open, rebuild, driving edits, save and fresh reopen. The
qualified combinations are a translated Front-plane diameter with forward
blind depth and a translated Top-plane radius with reversed blind depth.

The SOLIDWORKS 2026 SP05.2 run passes both controls, 14 fresh processes
and 400 recorded numerical checks. The original and generated files match
on the 25-row tree, native topology, configurations, geometry and the two
editable owners for each part. Sixteen strict normal SDK reads preserve
the actual centre and dimension owners and serialize all 32 scoped
streams byte-for-byte.

Use the frozen original method with the corrected topology observer for
reproduction. The method keeps the original writer and generated inputs
hash-identical through observer-only repairs. This result covers the
internal SDK profile and introduces no public writer registration or
qualified FCStd corpus count.

[Native lifecycle and the supported profile](../../../../../re/solidworks/records/SdkOriginalCircleNative2026.md)

[Sanitized native and SDK result](../../../../../re/solidworks/measurements/2026/SdkOriginalCircleNative01.json)
