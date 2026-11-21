# External light identifiers do not identify unique members

## Expectation

A light's external identifier can identify its unique native node and bind its revision history.

## Actual behavior

In each disclosed ordinary through-all source, the three directional nodes have distinct actual persistent IDs and captions but share the same `f4f8` external identifier. Native `getIdName` exposes this independent string. Matching it merges three different lights or attaches logs to the wrong node.

The ambient's `f388` is another independent setting: exact original getter/setter aliases bind it to keep-light-in-scene. The source value differs from the fresh type-one constructor; neither value can be substituted for every ambient light.

## Workaround

Reach the actual environment's ordered member collection. Preserve node identity, persistent ID correspondence and actual ownership. Carry the external identifier as a semantic string that may repeat. Bind source logs to actual generated nodes, and carry keep-light-in-scene as an explicit boolean rather than a constructor-derived universal value.

[Native field rules](../../../../../../re/solidworks/records/ThroughAllSystemMemberRules2026.json) · [Construction record](../../../../../../re/solidworks/records/ThroughAllSystemMembers2026.md) · [Process evidence](../../../../../../re/solidworks/measurements/2026/ThroughAllSystemMembers01.json)
