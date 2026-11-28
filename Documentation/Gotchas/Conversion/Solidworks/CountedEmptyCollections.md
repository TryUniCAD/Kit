# Zero counts still need empty collections

## Expectation

A loader can skip a zero-count collection body without constructing the collection.

## Observed behavior

The count writer derives its prefix from the collection length.
The 2026 feature-color and sketch-block map schemas skipped empty collection
construction on load, then failed during re-emission.
The [remote measurements](../../../../re/solidworks/measurements/ArchiveRoundTrip2026.md)
record both failures.

## Workaround

The shared length operation now constructs an empty collection when it reads zero.
The store derives zero from that collection and emits no element bytes.
Missing nonempty data remains an error.
Do not substitute recorded bytes or accept an unread tail.
