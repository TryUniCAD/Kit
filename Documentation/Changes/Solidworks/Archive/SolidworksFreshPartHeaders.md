# Fresh SOLIDWORKS part headers

The internal `MakePartHeads` constructor builds the typed `Header2`,
`Contents/Config-0-ModelHeader` and `Contents/CMgrHdr2` graphs for an
ordinary version-19000 part. Supply the allocated part, its actual
one-row configuration manager, explicit provenance and a part locator.
The existing archive codecs write the three graphs.

The two standalone roles use their own logs and share the same
self-file node. The directory derives its stamps and text from the
selected configuration and its part. Foreign owners, conflicting
selections, multiple or derived configurations and unsupported
configuration states raise an error.

Three guarded authored cases match all nine independently framed
streams. Consecutive reservations after the last allocation advance
both Header counters to the ID the allocator actually returns.
The existing L1 and ConcaveOwned controls retain six
exact streams in separate replay processes. Twelve guard cases
exercise the construction boundary. This change supplies internal
graph construction. Complete part emission and public writing
have separate acceptance conditions.

[Source and process evidence](../../../../re/solidworks/records/FreshPartHeaders2026.md)
