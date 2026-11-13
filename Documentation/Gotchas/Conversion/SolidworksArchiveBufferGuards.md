# Archive buffer guards

## Expectation

A `su_CArchive` buffer's current capacity should identify the exact length of a resolved-feature stream.
An exact-length breakpoint is tempting because older trace recipes used stream size as a buffer guard.

## Actual behavior

SOLIDWORKS 2026 can show a fixed `0x10000` capacity while reading an 11,205-byte resolved-feature stream.
The size guard therefore collects zero events despite a correct reader entry address.
The first value inside the resolved stream is the continuation `0x6d`, and its initial object-map index is 109.
Using a different file's size, fixed capacity, or an old process's transient string length silently suppresses relevant reads.

## Workaround

Identify the stream from its actual initial continuation and object-map data, not from the allocated buffer size or from a previous fixture's stream length.
Then validate the trace with nesting, zero gaps, and byte-identical symbolic re-emission.
See [the five-line result and trace](../../re/solidworks/records/PolylineFivePad.md) and [the native writer](../Changes/SolidworksFiveLineNativeHistories.md).
