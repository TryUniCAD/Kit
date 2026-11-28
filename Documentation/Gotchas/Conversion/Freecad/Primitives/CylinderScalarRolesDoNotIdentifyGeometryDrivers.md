# Cylinder scalar roles do not identify geometry drivers

The generic strict reader labels all thirteen scalar properties of the disclosed `Part::Cylinder` as driving parameters. That might suggest thirteen geometric dimensions, or that every field beyond radius and height can be replaced by its observed default.

The exact FreeCAD 1.1.4 source proves five geometric inputs: radius, height, sector angle and two oblique prism angles. `FirstAngle` and `SecondAngle` change horizontal displacement while the original circular base stays in its plane. A rigidly rotated right cylinder is generally different. Zero values do not turn those inputs into constants.

Other projected scalars have distinct ownership. Labels are user identity/description metadata; output status prevents geometry touch. Visibility controls show/hide rather than suppression. Attachment mode, reversal and path position are inactive inputs when the source is unmapped. The hidden engine class mirrors the enum but is also used to reconstruct it on restore.

Retain the original role, ID, unit and property tree, then classify each owner using the pinned source. Preserve target semantics explicitly or refuse the unsupported member. A metadata carrier alone does not prove live native preservation. The [rule record](../../../../../re/solidworks/records/FreecadCylinderPropertySemantics2026.md) and [offline receipt](../../../../../re/solidworks/measurements/2026/FreecadCylinderPropertySemantics01.json) identify the exact branch and evidence limits.
