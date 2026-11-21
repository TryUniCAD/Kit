# SOLIDWORKS 2026 separate note text border state

Both reached `moGenericText_c` constructors enable bit 10 of their `f160`
word after initializing earlier flags. The ordinary constructor does so at
`0x4bed3e73`. The alternate constructor does so at `0x4bed3b75`. The
exported `setIsSeparateBorder` leaf at `0x4bef1230` owns this bit.

`moGenTextHelper_w::getCurrentBorder` takes the actual text owner and checks
bit 10 at `0x4befac53` before looking for a border token. Enabling this
constructor default does not create a border token for plain text. The
independent layout-dirty bit 0 and the loader's last-newline bit 1 are
described in [the text metrics record](DrawingNoteFreshText2026.md).

The [numeric ledger](DrawingPlainNoteTextBorder2026.json) records the complete
constructor, setter and lookup spans on SOLIDWORKS 2026 SP05.2 and can be
replayed with [the original-image verifier](../../tooling/sw2026/InspectPartEnvironmentSource.py).
On-disk native sources also show bit 10. Fresh generation applies the
constructor rule without using source bytes. This field ownership does not
establish that the viewport renders the note.
