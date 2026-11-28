# Lightweight datum caches use a different transform encoding

## Expectation

The lightweight datum's transform uses the same compact encoding as its resolved principal plane.

## Observed behavior

The lightweight datum serializer calls the 30-word transform operator. Its alignment word varies in the native Top and Right copies, even when their principal matrices stay fixed. The compact resolved transform has no corresponding alignment word. [Layout and measured members](../../../../../re/solidworks/records/D01AssemblyLightweight2026.md)

## Workaround

Use the actual resolved plane geometry to build the operator's matrix and flags. Set the ignored word to canonical zero for fresh generation and retain the original words only for exact source inspection. Derive the displayed border in both members from the same real datum owner.
