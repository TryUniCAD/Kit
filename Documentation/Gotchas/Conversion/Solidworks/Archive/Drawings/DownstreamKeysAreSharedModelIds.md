# Downstream keys use a shared model allocator

A four-surface edge reference can identify the same analytic rail as a portable B-rep edge. Its drawing downstream key still cannot be calculated from that portable edge's ordinal.

Pinned 2026 creation initializes one model-wide next-ID counter, visits faces before edges, and increments the shared counter for new edges in native kernel enumeration order. Rebuild may reuse an earlier semantic edge ID and a free table slot separately. The attached kernel attribute also retains time and a distinct UUID-derived model-owner key; the archive stores that key in a different high/low word order.

Keep the geometric join separate from the numeric key. Preserve the typed source association on read. For generation, derive and validate one consistent ownership/allocation graph before emitting a populated detailing cache; do not seed keys from saved rows or SDK suffixes. The existing fail-closed unknown model-cache branch remains active.

[Exact allocation, attachment, persistence and remaining limits](../../../../../../re/solidworks/records/DrawingDownstreamIdentity2026.md) · [Source-only verification](../../../../../../re/solidworks/measurements/2026/DrawingDownstreamIdentitySource01.json)
