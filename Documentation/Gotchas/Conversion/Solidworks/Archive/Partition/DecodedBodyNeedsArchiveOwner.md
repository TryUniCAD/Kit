# Decoded partition geometry needs an archive owner

A SOLIDWORKS 2026 blind boss can have a complete decoded solid in the
selected configuration partition while its public feature has no output body
link and the public body has no topology counts or volume. The active
partition supplies the kernel geometry. The boss's saved output atom and
manager entry, together with the kernel's body identifiers, prove ownership.

Use the full native ownership chain before attaching body information. Compare
the selected geometry with the decoded packet at the appropriate stage. The
existing exact-cache comparison refused a rectangular control whose public
model already carried a design-body ID. Removing that one field difference
still left other differences in the graph. Keep independent checks of the
native graph and the neutral binding.
[Measured reader comparison](../../../../../../re/solidworks/records/VendorBlindBossAdmission2026.md#active-body-evidence)
