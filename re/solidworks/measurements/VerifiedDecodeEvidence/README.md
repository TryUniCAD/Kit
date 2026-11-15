# Verified SOLIDWORKS decode evidence

These 20 controlled part cases record what a historical offline decode recovered from seven supported combinations of SOLIDWORKS features and profiles. Each linked Markdown file contains a JSON object with a historical event ID, units, and a `cases` array. Each case includes a label, source SHA-256, reference archive SHA-256, model SHA-256, and the decoded neutral model. The records are research observations, not native stream layouts, vendor samples, writer inputs, or evidence of coverage in the current Kit runtime.

| Family                                    | Cases | Observable fields and relationships                                                                                                                                                                                                                      |
| ----------------------------------------- | ----: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Blind rectangle](BlindRectangle.md)      |     3 | One rectangle on a principal plane, blind depths of 12, 18, and 10 mm, and forward/reverse direction. The depth parameter belongs to the boss and its profile link points to the rectangle sketch.                                                       |
| [Blind pocket](BlindPocket.md)            |     2 | A 20 mm boss and a 10 mm cut in each direction. The boss and cut each have their own rectangle profile and depth parameter, even though the parameters share the name `D1`.                                                                              |
| [Blind circle](BlindCircle.md)            |     3 | One full circle with a 10 mm radius and a center-to-origin coincidence. Blind depths of 14, 16, and 18 mm are extrusion drivers; the circle radius is sketch geometry in these cases.                                                                    |
| [Blind ellipse](BlindEllipse.md)          |     3 | One full ellipse with an origin-to-center coincidence, explicit major-axis direction, and semi-axis pairs of 20/10, 24/10, and 20/12 mm. All three bosses have a 10 mm blind depth.                                                                      |
| [Two lengths](TwoLength.md)               |     3 | Two independent lengths on opposite sides of the support plane: 10/4, 14/4, and 10/7 mm. The saved first and second end owners distinguish the parameters; parameter name or listing order does not assign the roles.                                    |
| [Midplane](Midplane.md)                   |     3 | One total thickness of 10, 14, or 18 mm. The symmetric extrusion extends half the driving value to either side of the sketch plane.                                                                                                                      |
| [Boss with cap fillets](BossCapFillet.md) |     3 | A 20 mm rectangle boss and independently owned radii of 2, 3, and 5 mm. Both selected cap edges come from the same rectangle side. The connectivity-based mapping joins the actual selected side and cap roles instead of assuming a target edge number. |

## Licensing and attribution

These evidence pages and their [change entry](../../../../Documentation/Changes/Solidworks/VerifiedDecodeEvidence.md) use Kit’s [MIT License](../../../../LICENSE).
Copyright (c) 2026 Parashell, Odin Glynn-Martin.

## How the evidence was obtained

1. Controlled source cases supplied independent application measurements of feature parameters, profile or edge selection, and the rebuilt solid. These measurements checked the decode; they did not supply parameter values or choose owners during parsing.
2. The offline decoder followed typed archive references from the saved feature to its profile, support, end specification, and driving dimension. It preserved sketch geometry and constraints as separate editable records. The [archive grammar](../../archive/Grammar.md) and [serializer notes](../../records/Serialize.md) describe the underlying records; cached Parasolid geometry is a separate source of shape evidence.
3. Historical FreeCAD application checks opened the reconstructed editable models, compared rebuilt geometry and measurements, and exercised live driving edits. A later offline check compared complete neutral models and native archives to the accepted references and rebuilt them from generated Python with vendor source access revoked. For the fillet, volume alone could not distinguish opposite sides; the accepted check also compared selected edges, placement, and center of mass.

The immutable historical SDK freeze has SHA-256 `3a3b3c9800aaa57063fc4f854b946218712873bd76f5d4b6171fccefe74982ae`. The historical offline refresh receipt has SHA-256 `0f536a0bb836b963872b43073c5fb0355e7c737174facf98f395fcd28250da8b`. The corrected fillet application acceptance receipt has SHA-256 `bc606d65196229a71db6e8100b464e4da6083038f58f21dd112dfe70576d5475`. These identify archived campaign evidence; they are not claims about the current commit's runtime or checks.

Use the JSON to inspect field values, parameter and sketch ownership, and dependent feature order. The model SHA-256 identifies the `model` value serialized as UTF-8 JSON with sorted keys, no extra whitespace, and Unicode characters preserved. A populated `model.source.sha256` is an internal replay digest of the neutral model with that field cleared. The outer `source_sha256` identifies the original controlled source file.

The cases do not establish support for other versions, arbitrary sketches, end conditions, or histories. They do not establish strict lossless translation or a generative SOLIDWORKS writer. See the [porting notes](Porting.md) and [change entry](../../../../Documentation/Changes/Solidworks/VerifiedDecodeEvidence.md).
