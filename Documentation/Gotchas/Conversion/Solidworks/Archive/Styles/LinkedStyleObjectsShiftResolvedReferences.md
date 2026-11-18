# Linked style objects shift resolved references

A style-only graph change can alter the raw SOLIDWORKS ResolvedFeatures stream while leaving every feature field and reference target unchanged.

The ordinary linked archive shares its class/object counter from Config-0 into ResolvedFeatures. Creating eight owned dual-unit objects in Config advances that seed by eight. In the first generated normalization proof, Config's counter changed from 87 to 95 and Resolved's final counter changed from 236 to 244. Resolved retained its byte length while 53 bytes changed, beginning with the seed word. Both complete stream preparations passed. The first flow still rejected because it expected a part UI Definition change and no dependent Resolved change.

Recompute the linked maps and all tags through the existing codec. Verify the actual added Config owners and unchanged inherited classes, then compare the complete typed Resolved graph with explicit stable seed/object identities. Keep the complete presentation difference check. Do not patch tags by a captured offset, ignore arbitrary Resolved changes, or confuse the ISO-to-ANSI UI-owner delta with document-unit initialization.

The failed proof and corrected method retain both source freezes and the exact failure. The corrected method passes root's independent 32-process replay, requiring precisely eight added owned length units and every Resolved field and alias unchanged. Native style retention remains a separate pending measurement. [Method and evidence](../../../../../../re/solidworks/records/DrawingDetailNormalization2026.md)
