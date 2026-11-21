# Read plain SOLIDWORKS drawing notes in partial mode

Run kit decode SOURCE.SLDDRW --partial or call open_document with strict=False. On the measured SOLIDWORKS 2026 profile, the drawing contains one unlinked sheet and one unattached single-line note. The SDK exposes its stored text and metre position in DrawingSheet.Notes. It checks the actual note owner and the ordered UTF-16 text against the independent stored string.

The interchange JSON record preserves the text, coordinates and an ID derived from the owning sheet and list position. Older documents without notes keep their existing encoding. Native styling, model attachments, additional notes and note writing remain outside the supported profile.

Four disclosed sources and edited saves pass SDK and CLI partial reads, JSON transport and writer rejection. Twelve fresh process invocations pass. All 20 existing drawing research checks also pass. [Process evidence](../../../../../../re/solidworks/measurements/2026/DrawingPlainNotePublic01.json) · [Adapter usage](../../../../../Reference/Adapters/Solidworks.md#drawing-layout-inspection)
