# Snapshot body order carries separate passive identities

An XY circular two-sided extrusion has one live solid, but its saved snapshot contains three BODY roots: the solid, a double-sided profile sheet and a single-sided sketch sheet. Their physical root order is tied to `BRepSerializer.topEntityPIDGenerator.scanOrderIndex`. The IDs come independently from the extrusion tool's cached topology, the selected profile region's cached topology and `MSketch.bodyId`.

Matching geometry alone misses an ownership error. Swapping the two complete sheet roots and remapping every native reference preserves valid topology and both circles, but leaves the passive ID sequence attached to the wrong profile/sketch roles. It must refuse. Identify roles from their shells and face flags, then compare the scan sequence with the actual source-linked IDs. Check the cache scopes and the serializer's reciprocal component ownership as well.

The solid graph also differs from the live journal's record order and bookkeeping. Compare rooted reference walks, normalize absent snapshot entity tags and exclude only the separately validated live BODY attribute chain. Retain all face and edge feature tags, sketch source links, carriers and seam parameters. Both source sheets need their own complete attributed geometry checks and disjoint coverage.

The [bounded evidence](../../../../../../re/Fusion/DecodedPromotion20261127/DualAdmissionSnapshots/Rules.md) covers 54 XY drafted saved states and two controls, including six held-out parameter states. Five encoded counterexamples retain actual archives with wrong identity, feature tag, sketch source, body ordering or geometry. Twelve XZ states retain their refusal. These findings do not establish this layout for other features or qualify native conversion
