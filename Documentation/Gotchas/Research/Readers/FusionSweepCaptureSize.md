# sweep bend capture size differs after archive scrubbing

The SweepBend entry in CaptureSweeps.json reports 73,788 bytes. The committed archive is 73,787 bytes and matches the entry's SHA-256. ScrubLedger.json separately records the vendor-saved and committed digests. Code that verifies both export size and digest excludes this measurement. Preserve the receipt and use an independently pinned export for validation.
