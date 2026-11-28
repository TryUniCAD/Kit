# Archive maps initialize lazily

## Expectation

The native archive constructor's zero counter means the first class/object tag uses index zero, or a standalone body needs an explicit counter word to establish index one.

## Actual behavior

The pinned `su_CArchive` constructor initially writes counter zero with null pointer/load-array and schema-map members. Before the first pointer tag, `MapObject(NULL)` creates the reserved null slot zero and sets the next counter to one. Both a read-class operation and a write-object operation initialize this state before their ordinary tag handling. A null pointer operation also initializes it while allocating no positive entry.

A standalone downstream body is invoked directly and is not itself a mapped class/object. The first nonnull new-class object therefore gets class index one and object index two. The selected structured/zip, raw/compressed readers create fresh archives without Header/Config/Resolved map copies or a wire map-count prefix. If no pointer operation is reached, native physical state may remain uninitialized even though a pure codec represents the equivalent null-reserved logical namespace.

## Workaround

Use the existing unseeded `ArchiveMaps(1)` for the selected standalone codec, preserve shared class/object allocation and identity, and invoke the downstream root's body directly. Keep physical lazy-state observations separate from the SDK's logical map count. Do not register a dummy root, bind Header aliases, use zero as a positive reference, or insert an extra count word.

The [exact native/source record](../../../../../../re/solidworks/records/DownstreamStandaloneMaps2026.md) supplies the bounds and limits. This is a selected standalone-read rule, not permission to change Config, Resolved, DB or copy/add-configuration contexts. Complete saved-stream replay and native acceptance remain pending.
