# Compare physical concentric source faces

The disclosed D01 research comparison binds each source cylinder face to the corresponding face of an independently generated child. It uses the real sketch support and extrusion extent to distinguish the two physical caps and verifies their complete circular trims. Each ordered selection retains its actual occurrence, local and world axis, and source provenance.

Run `re/tooling/sw2026/para/concentric/ProveConcentricSourceBrep.py ORACLE_RECEIPT_DIRECTORY NEW_SCRATCH_DIRECTORY` in the locked Python environment. It verifies the existing disclosed receipts, builds fresh child geometry offline and records the face mappings and unsupported cases. Four comparisons pass across 12 faces and eight endpoints. Six deterministic child builds make zero guarded runtime input accesses. The whole-source assembly remains outside writer admission.

[Field ownership and host evidence](../../../../../re/solidworks/records/ConcentricSourceFaceCorrespondence2026.md)
