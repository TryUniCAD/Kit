# Native circle sketches retain point entities

Expected: the first neutral sketch entity is the full circle.

Observed: strict reading preserves the native origin/centre point entities before the circle. A new edit fixture therefore failed all 22 radius-edit cases by selecting a point as its profile.

Resolve the declared closed profile or select the unique qualified circle by type. Preserve the point entities and their distinct IDs; do not reorder or remove source records to fix a fixture.

[Failed fixture and retained native observations](../../../../../re/Fusion/DecodedPromotion20261127/RimPublic/README.md)
