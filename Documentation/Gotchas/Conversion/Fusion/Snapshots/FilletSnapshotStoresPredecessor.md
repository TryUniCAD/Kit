# Rim fillet snapshot stores the predecessor cylinder

Expected: the saved solid snapshot matches the final rounded body and exposes the same specialized snapshot convenience fields.

Observed: these sources store the pre-fillet cylinder plus separate profile/sketch sheets. Some use `SnapshotModel`; others use generic `GeometryState`. The selected live predecessor edge also has an owned tracking attribute absent from the snapshot.

Resolve actual snapshot roles from typed topology. Validate the reciprocal selected-edge tracker before removing only that record in a reversible canonical comparison. Compare every remaining carrier, topology link and source tag, and cover both sheets with no unowned records. The existing cached topology/snapshot link checks still apply; additional matrix/circle caches do not imply additional topology caches.

[Recorded rule and representation failures](../../../../../re/Fusion/DecodedPromotion20261127/RimFilletGeometry/Rules.md)
