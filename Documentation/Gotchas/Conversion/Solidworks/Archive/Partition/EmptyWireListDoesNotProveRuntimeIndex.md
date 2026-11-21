# Local owner indexing depends on runtime insertion order

The generated ordinary part supplies `n_ext=0` and an empty CMgr external list. That loader branch adds no incoming entries. The first local insertion into a fresh list receives index zero.

Derive the owner from the actual live table. If a different file has already been inserted at index zero, the resolver can return it. A missing lookup falls back to the local owner under the selected repair conditions. [Source and remaining load interval](../../../../../../re/solidworks/records/DownstreamLocalOwnerIndex2026.md)
