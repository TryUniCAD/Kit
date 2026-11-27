# Reversed blind-boss preparation

The neutral SOLIDWORKS part constructor now retains `ExtrudeFeature.reversed` for its bounded single blind boss.
It emits direction from that Boolean through the existing typed end constructor.
Depth remains positive, and the start type remains zero.

The supported preparation profile remains one canonical Front-plane line loop, one blind boss and one solid.
Explicit contradictory direction vectors, symmetric extents, offsets and non-Boolean reversal values refuse preparation.
The constructor reads no captured native payload or donor template.

This change prepares candidate bytes inside the existing SDK writer pipeline.
Public `write_document` and `kit convert` still require a trusted native measurement receipt for the exact regenerated archive.
A forward receipt cannot authorize a reversed archive.
The writer preserves the destination when the receipt is missing or mismatched.

Six complete archives cover three profiles in both directions.
Strict SDK readback verifies signed bounds, centroid, volume, owned depth and neutral JSON restoration.
Cold readback followed by preparation reproduces all six committed archive hashes.
Two authentic measured forward models retain their exact hashes.
Their receipts reject reversed candidates through both direct and registered writers.
Three fresh CLI processes also reject unmeasured reversed neutral documents without changing existing destinations.

The [retained preparation evidence](../../../../re/solidworks/DecodedPromotion20261127/Preparation/Receipt.json) records source hashes and failures.
Coverage uses `tests/Convert/Solidworks/PlainWriting/ReversePrep` through the existing shared test-suite and merge-queue path.

The CAD API is unavailable.
Native reversed-file edits, restoration, rebuild, save, independent holdouts and fresh-process reopen remain unexecuted.
Preparation and successful decoding do not establish conversion acceptance.
The [measurement gate](SolidworksMeasuredPartPublication.md) remains authoritative.
