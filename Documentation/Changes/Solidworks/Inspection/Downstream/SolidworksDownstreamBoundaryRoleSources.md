# SOLIDWORKS conditional downstream boundary sources

The [source checkpoint](../../../../../re/solidworks/records/DownstreamBoundaryRoles2026.md) distinguishes permanent-edge, sketch-pointer and downstream-edge attributes. It pins actual previous/next loop traversal, conditional start/end face roles and when a fresh edge's downstream attribute is attached after its reference and row are built.

For an explicitly fresh ordinary graph with no permanent-edge attributes, the role recipe follows actual fin links and already allocated face IDs, retaining duplicate face IDs under distinct keys. Later ambiguity/reference replacement and other unproven branches remain outside the recipe. No public reader or writer behavior is enabled by this research delivery.

Use `re/tooling/sw2026/downstream/VerifyBoundaryRoleSources.py` with the pinned licensed original files and a new output path. The [receipt](../../../../../re/solidworks/measurements/2026/DownstreamBoundaryRoleSource01.json) records 61 complete function entries and 108 checked intervals, with zero CAD input reads, SDK product runs, native processes or VM calls. No vendor bytes or listings are included. Native output acceptance and original-source conversion are not claimed.
