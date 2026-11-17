# Source relabeling does not resolve semantic evidence

This records preserved decoder follow-up behavior at `fb723e0a920b4d03ad2d5635882860b800a9b61c`. Its decoder and writer changes are outside the main-based automation candidate.

## Expectation

A document that retains unresolved equation references, equation targets or dimension units remains ineligible for interchange export after its source format is relabeled.

## Observed behavior

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576681680) identified that the equation and inch write guards only inspected documents whose source format was `solidworks.sldprt`. Source inspection confirmed that JSON persistence preserved the native markers, while a different source format bypassed those guards.

## Workaround

Evaluate retained semantic markers independently of the mutable source label. Apply the same checks to embedded documents and direct and registry writers before output mutation. Preserve the evidence for inspection until independent qualification resolves the underlying semantics.

See [the change entry](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Changes/Research/ReidentifiedWriteMarkers.md).
