# A verified Python runtime does not enable the personal CAD transport

## Expectation

The correct installed Python 3.14 Kit executable appears sufficient for native verification.

## Observed behavior

The direct executable used local application discovery and reported unavailable APIs.
The configured personal launcher separately enables the existing transport adapter.
A correct interpreter alone did not select that adapter.

## Workaround

Use the configured personal launcher with an explicit trusted research root.
Invoke its shell interpreter when the saved launcher lacks executable permission.
Verify that it delegates to the installed Python 3.14 executable.
Preserve earlier unavailable outcomes.
Do not replace decoder results or relax native checks.

See the [campaign record](../../../../../re/CutsRevolutions2026/README.md) and [runtime shadowing](ShadowedKitLauncher.md).
