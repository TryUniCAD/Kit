# Circle endpoint uses do not count adjacency clones

## Expected

Two endpoint uses of one circle marker create two retained adjacency handles.

## Observed

The native endpoint registrar checks for an equivalent segment handle before allocating another clone.
A circle's opposite endpoint resolves the same point.
Its first registration creates `h1`.
The opposite-point check then finds that handle, and the later endpoint role also reuses it.
The point-use counter still increases twice.
In the bounded ordinary branch, `h2` stays null.

This corrects an earlier two-clone inference in the research construction ledger.
All 24 completed source circles agree with the corrected static prediction.
The [native finding](../../../../../re/solidworks/records/CircleAdjacencyRegistration2026.md) records complete function hashes, class dispatch, prerequisites and unresolved acceptance.
Static agreement does not observe execution or establish generated held-out acceptance.

## Workaround

Track role-use counts separately from retained equivalent-handle membership.
Preserve object identity for each clone that is actually allocated.
Require the native admission and insertion conditions before applying this rule.
Keep serializer cleanup separate from this deduplication rule.
