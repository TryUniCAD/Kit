# Audit typed SOLIDWORKS configuration directories

The [corpus auditor](../../../../re/tooling/sw2026/AuditManagerDirCorpus.py)
reads and re-emits each `Contents/CMgrHdr2` directory through the SDK's
scoped codec at a pinned code revision. It compares the complete
stream and map on the 80 disclosed parts and eight assemblies.

All 88 directories round-trip exactly. Each has one concrete
configuration header. The integrated binary audit retains all 1,328
exact stream replays. The disclosed corpus establishes this directory
shape and its field encoding. The independently authored extended
count test remains separate from the single-child corpus observation.

[Configuration directory census](../../../../re/solidworks/measurements/2026/ManagerDirectoryCorpus01.json)
· [Integrated binary audit](../../../../re/solidworks/measurements/2026/BinaryArchiveAfterManagerDirectory01.json)
