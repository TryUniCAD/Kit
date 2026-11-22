# Resuming field discovery after an opaque range

When contiguous text ends, the research command searches up to 64 bytes ahead for a unique counted-text encoding on both discovery streams. It resumes from the end of each decoded field and records each skipped range separately. The generated reader replays the frozen sequence of relative skips and encodings on the remaining controls. A disagreement on a later field prevents patch publication.

On the P03 native Fusion active manifest, 17 fields account for 532 of 589 bytes. Nine non-text ranges total 57 bytes. A reader reaching the end of the manifest still does not establish meanings for those bytes or coverage of the whole F3D archive.
