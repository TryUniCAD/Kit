# Unbound body display label

The strict SDK read of the pinned SOLIDWORKS P03 baseline reports `Body 1` with no body provenance or native object ID. The reached Config-0 atom is numbered 101 and belongs to Boss feature 34. Its saved compatibility label and independent implicit kernel label both read `BlindBoss`. The active body has no explicit authored rename.

Check actual body ownership and label source before transferring an SDK fallback into a writer. Keep the unbound display fallback, implicit saved label, and any independently proven authored name distinct. For this baseline, the bounded research writer binds the compatibility label from its active atom and keeps the original fallback in the source evidence. [Constrained Boss candidate](../../../../Changes/Research/Encoder/ConstrainedBossCandidate.md)
