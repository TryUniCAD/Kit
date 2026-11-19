# Ordinary plain drawing note source protocol

Task `B04-SW2026-DRAWING-NOTES`, owner the PR #121 takeover agent. The deliverable
is an independent 2026 native source lock for one unattached sheet note with
editable text and position. The [native attached-edge lifecycle](DrawingAttachedNoteDepth2026.md#native-lifecycle)
already covers a separate component-owned attachment. This plain note protocol
targets the actual sheet owner.

Use the reserved Windows 11 oracle and the pinned installed ANSI A blank
drawing template. Copy [the source tool](../../tooling/sw2026/drawing_notes/AuthorPlainDrawingNotes.py)
and the four shared dependencies it declares under a fresh packet's `Tools/`
directory. The exact pristine D00 drawing belongs at `Control.SLDDRW`. Bind all
five source hashes, the installed template and current pre-writer commit in
`Job.json`. The two disclosed cases supply authored note text and position.
The two held-out choices are created under a new guest-local C: directory with
independent text and position, and are reduced to hashes in the shared receipt.

Run `verify Job.json --sha256 <hash>` before native execution. Then
`run Job.json --sha256 <hash> --receipt <unused receipt path>` executes the
bracketing controls and the author, edit/save and fresh reopen phases in each
case. The application must expose exactly one sheet annotation, with attached
entity count zero, two independently set positions, and zero rebuild, save and
open diagnostics. Native-edited derivatives remain separate from their original
source files. Source and edited hashes are locked only after all their checks
pass.

The initial packet records source chronology. Native note decoding, neutral
construction and qualification of generated notes are subsequent work.
