# Derived body names on cache-free SOLIDWORKS revolves

Strict reads with B-rep enabled now keep the printable ASCII name of
the actual creating feature on the reconstructed body of a supported
ordinary rectangular revolve. The existing body-binding rule verifies
the sole solid, its design body and its last feature before publishing
the derived label with the creator's provenance.

The guarded host comparison used four exact disclosed cold parts and
two independently authored labels. Twelve projections changed only
the derived label, its provenance and the resulting document hash.
Twenty-eight other reads and refusals remained exact. These include
saved named bodies, history-only reads and a non-ASCII cold label.

Explicitly named revolves, conflicting owners, non-ASCII derived
labels and additional bodies retain their existing boundaries.
This is a reader change with no new native application acceptance.
[Evidence](../../../../../re/solidworks/records/SdkColdRevolveNames2026.md)
· [Producer handoff](../../../../Gotchas/Conversion/Solidworks/Geometry/ColdRevolveNeedsProducerForName.md)
