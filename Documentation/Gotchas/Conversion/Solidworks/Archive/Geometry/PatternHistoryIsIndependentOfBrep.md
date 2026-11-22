# Cold pattern history is independent of B-rep

A design-only SOLIDWORKS read can omit a derived B-rep while retaining
the same native feature timeline and drivers. For a cache-free pattern,
skipping the linked history decoder with `include_brep=False` loses
the stock, datum and pattern ownership the caller still requested.

Apply the same typed history checks to either strict read mode. Omit
only the derived B-rep and its capability for a design-only request and
compute that projection's semantic fingerprint. When republishing, compare
the entire document with a fresh strict decode in the same geometry mode
and require an exact measured archive receipt.

Complete the neutral timeline and presentation binding before accepting
a typed cold result. A keyword caption can contradict the linked
feature name after the archive graph has decoded. Strict reads report
that cause. Permissive reads restart from the ordinary feature model
and discard the provisional typed history and analytic body.

[Measured pattern readback](../../../../../../re/solidworks/records/MeasuredLocalLinearPattern2026.md)
