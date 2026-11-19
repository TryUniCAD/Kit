# Author independent plain drawing note sources

The SOLIDWORKS 2026 research protocol authors two disclosed and two guest-private
drawings, each with one plain note placed directly on a blank ANSI A landscape
sheet. The note belongs to the sheet and has no entity attachment. The protocol
checks text, coordinates and identity through rebuild, an independent text and
position edit, save and fresh reopen.

Run `AuthorPlainDrawingNotes.py` with a SHA-256-bound job inside the reserved
Windows guest. Each launch checks the installed oracle build, and the job
requires the exact installed drawing template, pristine drawing and tool
closure. The source receipt reports hashes and phase identities. Private note
values and the corresponding saved drawings stay on the guest. This protocol
establishes pre-writer source custody for the plain note family.
[Source procedure](../../../../../../re/solidworks/records/PlainDrawingNoteSourceProtocol2026.md)
