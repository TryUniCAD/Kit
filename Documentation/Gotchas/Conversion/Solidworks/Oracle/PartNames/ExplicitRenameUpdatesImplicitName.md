# An explicit body rename also changes the implicit label

An explicit `IBody2.Name` save might appear to add only `SDL/TYSA_NAME`. In both disclosed SOLIDWORKS 2026 rectangular designs, that save also changes field zero of the existing body-owned `SWIMPLICITBODYNAME_ID_U` attribute to the same text. The actual `moAtom_c.f18` gains the authored `moNodeName_c` holder and `f18c` changes from one to zero. `SW_INTERNAL_BODY_NAME` remains absent.

Inspect all actual owners. Do not treat one character-vector insertion as proof that a generated named body needs no other state. A reader must distinguish authored, explicit and implicit names and keep conflicting-name precedence unqualified until measured. The native body-assignment path can propagate the resolved atom name, but no-cache regeneration still requires a controlled measurement.

[Complete typed ownership and source evidence](../../../../../../re/solidworks/records/NamedBodyOwnership2026.md)
