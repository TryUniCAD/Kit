# A first part save can leave the encoded self locator empty

The first `SaveAs` of a newly authored SOLIDWORKS 2026 SP04.1 part wrote an empty `Header2` self locator.
A subsequent `Save3` recorded the full locator in `Header2`.
Both files reopened with the same profile, driving depth and solid measurements.
Fifteen clear streams differed between those captures.

When measuring no-op save variation, save the owned document once after its initial save before collecting both snapshots.
Check the encoded self locator and part measurements across the pair.

[Native corpus evidence](../../../../../../re/solidworks/measurements/2026/VendorBossCorpus/SourceContrasts.json)
