# Read saved SOLIDWORKS single edge fillets

Strict geometry reads of the measured constant-radius fillets on
axis-aligned rectangular stock retain the editable D1, actual preceding
stock edge and named result body. The SDK follows both native stock and
fillet stages. It derives the two actual circular trims from their stored
sense and validates their quarter-round geometry.

The bounded path applies to ordinary version-19000 native saves with a
single Default configuration, one convex full-length stock edge and a
complete matching active partition and rollback. Four guarded reads agree
with the disclosed SOLIDWORKS 2026 SP05.2 topology and twenty independent
volume, area and centroid measurements to six significant figures.
[Readback method and receipt](../../../../../re/solidworks/records/SavedEdgeFilletSdk2026.md)
