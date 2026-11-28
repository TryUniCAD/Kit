# Finite hinge sizing follows the first selected plane

## Expectation

The infinite plane intersection appeared sufficient to calculate the two-plane reference axis used by the angled datum.

## Actual behavior

Both selected geometric planes determine the infinite line. In the measured local path the first selected wrapper supplies its finite display rectangle. The directed distances and endpoints depend on that rectangle. The principal border size uses `span*0.5 + span*0.05`. Combining those terms into one multiply changes a measured 90 mm span by one binary64 unit in the last place. [Static and native source evidence](../../../../../../re/solidworks/records/LocalLinearPatternFiniteHinge2026.md)

## Workaround

Preserve the actual first and second wrapper roles and the principal display sizing order. Record the finite limits at the hinge insertion stage before using them to construct the angled datum.
