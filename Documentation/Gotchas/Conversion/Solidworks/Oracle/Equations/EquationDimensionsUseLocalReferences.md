# Equation dimensions use local reference handles

## Expectation

An equation wrapper can point directly to the dimension handle owned by the sketch or feature.

## Observed behavior

The SOLIDWORKS 2026 wrapper factory clones the live dimension handle.
It binds the clone to the model's local component.
The wrapper stores the clone, and the feature retains its own handle.
The two handles still identify the same dimension.

Both disclosed native saves retain this pattern for feature depth and sketch width.
The ordinary feature handles have a null component field.
The equation handles point to distinct local components with the same model owner.

## Workaround

Construct the equation handle from the generated driver identity and the actual model owner.
Retain the shared feature dimension or sketch and its dimension ordinal.
Keep the original feature handle intact.
Use the complete configuration map when writing ResolvedFeatures.

[Native constructor and archive evidence](../../../../../../re/solidworks/records/PartEquationConfig2026.md#local-dimension-reference-handles)
