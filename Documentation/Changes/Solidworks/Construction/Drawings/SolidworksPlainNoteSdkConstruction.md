# Internal SOLIDWORKS drawing note construction

The typed SDK constructor `MakePlainNoteFile` builds one printable, unformatted
note on an unlinked landscape ANSI A sheet. It composes the sheet and its
metadata with the existing blank drawing constructor and extends the actual
sheet detail folder with a distinct note name, display identity, text tokens,
and computed position. The existing drawing Definition serializer emits the
complete object graph and derives its map.

For controlled evaluation, run the [guarded SDK worker](../../../../../re/tooling/sw2026/drawing_notes/BuildNoteSdk01.py)
with an explicit note-intent JSON, its SHA-256, an unused output and receipt, and
the [writer guard directory](../../../../../re/tooling/sw2026/blank_eval/rewrite).
The worker independently checks the emitted Definition bytes and archive map
through read and re-emission, and the ordinary partial drawing reader checks
the resulting text and position.

Four independent SDK processes produced two byte-identical pairs with zero
writer input reads. Both pairs matched their disclosed research generator
controls across all seven logical streams and the containers. Different text
lengths produce Definitions of 27,770 and 27,350 bytes with map counters of 176
and 166. The first exact container already passed a disclosed native
open, edit, save and fresh reopen. The second was measured on the host.
See the [SDK receipt](../../../../../re/solidworks/measurements/2026/SdkPlainDrawingNoteConstruction01.json)
and [native receipt](../../../../../re/solidworks/measurements/2026/FreshPlainDrawingNotePositionNative01.json).

This constructor is internal. Public blank output and partial drawing inspection
retain their existing admission. Original source preservation, rendering and
its ordered feature tree require separate native evidence on the locked drawings.
