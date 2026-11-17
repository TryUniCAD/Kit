# Compare synchronized reference stamps with their exact child files

The [synchronized source procedure](SolidworksSynchronizedAssemblySources.md)
keeps each populated assembly and its separately saved child together. The
discovery preparer admits only the empty, single and repeated parent files
and the two associated child files. It verifies the source lock, records
same-width metadata redactions, and opens only the container while preparing
the fixtures. The held-out payloads stay outside preparation and CI. The
[preparation receipt](../../../../../re/solidworks/v2026/corpus/assembly-synchronized/SourceEvidence.json)
binds 207 streams, 85 redactions, and five visually inspected previews.

The remote reader compares seven archive streams per file and tracks the
parent's linked reference identities through the configuration map. It
reports whether each saved reference's update counter, update time and
geometry counter match the corresponding fields in its actual child. The
comparisons are observations, with no imposed equality for an unproved
native field rule. These fixtures add no generated assembly or writer
acceptance. Remote evidence is pending.
