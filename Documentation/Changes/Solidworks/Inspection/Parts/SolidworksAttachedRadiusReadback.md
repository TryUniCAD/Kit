# Read attached SOLIDWORKS radius bosses

Strict SOLIDWORKS part reads can preserve the live radius and blind depth of
an ordinary forward Front-plane circle with one attached Parasolid solid.
The reader resolves both `D1` parameters to their actual archive objects and
joins the visible configuration atom, feature, implicit body name and
active rollback state. Geometry reads keep the physical cylindrical solid
and compute its analytic volume, area and centroid. Design-only reads keep
the same parameter and feature identities.

The disclosed frozen child and its native-saved derivative passed the
SDK reader in separate guarded processes with exact typed data and no
external input after imports. Both states matched the geometry observations
from SOLIDWORKS 2026 SP05.2 while the child was resolved in its assembly.
The reader explicitly retains the inactive blind depth after a live depth
edit. Presentation entries remain outside the editable-feature proof.

This is input-reading coverage. Standalone SOLIDWORKS acceptance and
native writing remain separate.

[Measurement and scope](../../../../../re/solidworks/records/AttachedRadiusChild2026.md)
