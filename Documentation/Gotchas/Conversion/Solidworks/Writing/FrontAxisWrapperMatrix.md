# A principal axis may select Front without a stored matrix

The shared two-plane hinge builds wrappers for Top and Right, where
the typed transform includes the explicit matrix branch.

The measured F14c X and Y axes select the actual Front plane. Its
wrapper still has the outer transform, with `has_matrix=0` and no
inline matrix field. The support identity, creation stamp, finite
borders and normal still come from the same real datum.

Use the explicit Front identity branch when the generated selected
owner carries that transform. Reuse the same wrapper and creation-log
rules for the populated Top and Right matrices.
[Controlled native and strict read evidence](../../../../../re/solidworks/records/AttachedBoxAxisRead2026.md)
