# Native scalar kind handling

## Expectation

A recovered native scalar can be converted into a length-bearing neutral parameter whenever it has a binary value.

## Actual behavior

`instance_count` is already a count rather than an angle or length. Applying `native_value * 1000` and the millimetre unit produces both the wrong numeric value and the wrong unit when a pattern count is bound to its native scalar. Angle conversion is different again and must use degrees.

## Workaround

Handle `instance_count` before angle or length conversion and return `ParamValue(Dimension.value_mm, NUMBER, "")`. Only apply the raw-scalar millimetre conversion to length-bearing dimensions, and convert native angular values to degrees. Preserve the presentation value as the fallback when no native scalar is available.

This kind distinction complements `RecoverTriDepth` rather than promoting every native field to a length. Pattern semantics need independent feature and parameter checks, not a special exemption for dimension-looking names.

See [the adapter](../../../../src/convert/adapters/solidworks/core/Adapter.py), [the native depth gotcha](SolidworksTriangleDepthRecovery.md), and [native replay acceptance](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
