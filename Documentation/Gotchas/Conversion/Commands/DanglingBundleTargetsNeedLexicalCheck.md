# A dangling bundle destination needs a lexical check

## Expectation

A dangling link at the requested assembly filename occupies that output entry.

## Actual behavior

The shared staging API resolves the requested destination before checking
the resolved path for occupancy. A dangling link can resolve to an unused
filename in another directory. The original link then lies outside the
resolved directory scan.

## Workaround

Inspect the literal requested root before entering path staging. The nested
publisher rejects that link and leaves both the link and the referenced
location untouched. The stage emitter checks all final companion filenames
in the resolved sibling directory.
[Guarded root-link case](../../../../re/solidworks/measurements/2026/SdkNestedAssemblyPublication01.json)
