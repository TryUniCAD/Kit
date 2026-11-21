# Square revolve profiles can carry an extra equal-length relation

The matched rectangular controls carried four unary horizontal and vertical relations. Three separate native squares also carry a live binary equal-length relation on two perimeter sides. SOLIDWORKS reports `swConstraintType_SAMELENGTH` with code 14. The saved relation is one `dims.log_g2` row with two concrete local line handles. Each referenced line has two solver references because it also owns a unary relation. [Square source evidence](../../../../../../re/solidworks/records/RevolveEqualLengthRelations2026.md)

Preserve the relation and its ordered entity references in the neutral sketch. Validate both the unary and binary groups against actual line incidence. Derive reference counts from all emitted relation owners.
