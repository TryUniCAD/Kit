# Strict Fusion reads can omit physical stream spans

## Expectation

A successful strict neutral read can appear to provide all physical stream provenance available for the source.

## Actual behavior

Strict reads of RequestedCorner and SavedCuboid produced valid feature graphs and zero physical member spans.
Partial reads of the same files cited 61 and 28 spans respectively.
The old file scope report treated the complete member inventory as uncited when it used only the strict document.

## Workaround

Use the strict document for feature selection and consult source-bound partial spans for physical coverage.
Check the source digest, member name, and span bounds against the same container.
Keep the partial document's research status and require independent evidence for feature qualification.

See the [file scope change entry](../../../Changes/Research/Encoder/FileScopeAttribution.md).
