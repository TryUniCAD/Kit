# Circle marker collisions use index-specific bounds

## Expectation

A point-within-tolerance query could appear to use Euclidean distance and identical endpoint rules for every index.

## Observed behavior

The 2026 circle-marker search intersects independent X and Y ranges.
A corner point can qualify even when its Euclidean distance exceeds the tolerance.
For 2D sketches, the query ignores Z.

The new coordinate-tree index includes each lower endpoint and excludes each upper endpoint.
The legacy sorted-array index includes both endpoints.
Both compute their bounds with separate binary64 additions and subtractions.
An absolute-difference comparison can change a boundary decision.

The query also filters point types and lifecycle flags.
Type-two circle markers do not obstruct candidates.
Ordinary eligible endpoints and centres can obstruct them.

## Workaround

Use the native eligibility predicate and the selected index's range conditions.
Derive coordinates from the local neutral sketch.
If the native index choice is unavailable, require both endpoint rules to select the same marker.
Keep a boundary-sensitive result unproven until that dependency is resolved.

The [marker placement record](../../../../../re/solidworks/records/CircleMarkerPlacement2026.md)
contains the exact predicates, module hashes, instruction anchors and remaining environment dependency.
These static rules do not establish a generated curve's native acceptance.
