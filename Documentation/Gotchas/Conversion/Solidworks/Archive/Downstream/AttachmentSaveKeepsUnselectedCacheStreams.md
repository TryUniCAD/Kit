# Attachment save keeps unselected cache streams

## Expectation

The assembly attachment downstream method removes an absent or stale cache stream, like the separately bound part method.

## Actual behavior

In the pinned 2026 `SolidStorage_c::SaveDownstreamIdDataForAttachment`, document/configuration/attachment/cache eligibility checks occur before stream attachment. A missing or stale attachment cache returns zero with no `destroyNode` call. The part method has a separate deletion branch. A stream that remains in storage therefore does not prove that the attachment cache was freshly serialized.

The attachment method can also return one after stream creation while autosave skips the direct body. Its caller does not test that return. A positive return alone is not a persistence witness.

## Workaround

Keep the two lifecycle rules distinct. Bind the actual configuration, opened attachment owner and cache freshness. Require a saved-stream/body observation before reporting persistence; preserve any pre-existing stream and the unmeasured result explicitly.

The [source record](../../../../../../re/solidworks/records/DownstreamAttachmentStore2026.md) gives original function extents, caller gates and hashes. This finding changes no preference, SDK behavior or acceptance state.
