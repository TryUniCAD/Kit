# A literal vector takes precedence over selected direction

`moDirectionSpec_c::getUpdatedDirection` checks persistent `f18` first. A present literal vector bypasses live line and plane selection, removing those features' control over extrusion direction.

The reference-taking constructor stores the actual wrappers at `f08` and clears optional numeric geometry `f18/f20/f28`. Retain that representation for direction driven by editable datums. [Exact-build source](../../../../../../re/solidworks/records/FreecadCylinderDirectionWire2026.md)
