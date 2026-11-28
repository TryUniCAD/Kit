# Read attached SOLIDWORKS radius bosses

Strict SOLIDWORKS part reads can preserve the live radius and blind depth of
an ordinary forward Front-plane circle with one attached Parasolid solid.
The reader resolves both `D1` parameters to their actual archive objects and
joins the visible configuration atom, feature, implicit body name and
active rollback state. Strict reads compare the physical radius and signed cap
span with the live drivers in both modes. Geometry reads retain the solid and
its analytic volume, area and centroid. Design-only reads return the same
parameter and feature identities without the B-rep payload.

The disclosed frozen child and its native-saved derivative passed the
SDK reader in separate guarded processes with exact typed data and no
external input after imports. Both states matched the geometry observations
from SOLIDWORKS 2026 SP05.2 while the child was resolved in its assembly.
The reader explicitly retains the inactive blind depth after a live depth
edit. Presentation entries remain outside the editable-feature proof.

A tracked shared-queue subprocess verifies the strict and permissive
outcomes for an independently constructed attachment whose physical
transmit profile is unsupported. The disclosed original and edited
files also pass the guarded SDK reads. Typed radius and depth conflicts
fail both read modes while retaining the original physical payload.

Standalone SOLIDWORKS qualification and native writing for this
profile remain pending.

[Measurement and scope](../../../../../re/solidworks/records/AttachedRadiusChild2026.md)

Strict reads reject invalid typed ownership in the recognized attached radius
lane. Raw B-rep extraction keeps strict payload framing without requiring
typed driver agreement. The linked-radius process check covers a broken atom
owner in both strict read modes.

Full geometry reads reuse the decoded cylinder and its driver comparison only
when the selected partition digest matches. The full read still validates the
raw shell owner. The disclosed-input worker checks for repeated decoding.
