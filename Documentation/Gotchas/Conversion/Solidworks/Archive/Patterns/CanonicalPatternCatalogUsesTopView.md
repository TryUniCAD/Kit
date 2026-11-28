# Canonical cache-free pattern catalog uses the Top view

The proposed canonical SOLIDWORKS 2026 pattern writer emitted `*Top` then `*Back`. Direction, profile and geometry were correct, yet strict geometry initially refused both parts because the recovered earlier pattern branch expected `*Front` and `*Back`.

Validate the actual canonical orientation, pan, identity and annotation memberships when admitting the additional catalog. Preserve the existing catalog for earlier sources. Keep the geometry refusal when a recognized view name carries an incompatible transform or owner. [Canonical read contrasts](../../../../../../re/solidworks/measurements/2026/SdkCanonicalColdPatternRead01.json)
