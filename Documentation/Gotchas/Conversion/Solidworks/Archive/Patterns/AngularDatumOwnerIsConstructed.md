# The angular datum backlink belongs to construction

The generated angular datum data has an `owner` backlink to its concrete plane. The archive stores that relationship through the plane's typed `f6f8` field. The reciprocal archive read restores the geometry and the containing datum while leaving the in-memory backlink absent.

Require the actual backlink when constructing a new selected direction wrapper. For geometry readback, follow the concrete `f6f8` field. Both routes use the same ordered display-rectangle rule. [Evidence and shared construction](../../../../../../re/solidworks/records/LocalLinearPatternPlaneDirectionRule2026.md#shared-archive-construction)
