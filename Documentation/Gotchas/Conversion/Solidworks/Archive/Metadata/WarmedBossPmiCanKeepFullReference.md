# A warmed blind boss can retain its full PMI reference

Both warmed no-op saves of an ordinary SOLIDWORKS 2026 SP04.1 polygon boss
had an initialized self locator. The independently read PMI database held
one complete `D1@Boss-Extrude1` annotation in each file. Both records still
included the document title and configuration reference.

Read and verify the actual PMI reference fields. A populated Header2 locator
alone does not select the short PMI record form for an unconstrained profile.
Check that the record names the same dimension owner and uses its unrounded
value.
[Measured PMI comparison](../../../../../../re/solidworks/records/VendorBlindBossAdmission2026.md#pmi-and-exchange-records)
