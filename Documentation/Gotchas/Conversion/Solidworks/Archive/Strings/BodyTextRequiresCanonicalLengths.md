# Body text requires canonical CString lengths

The CString reader accepts a count encoded with a longer prefix.
The ordinary wide writer selects a prefix of one, three or seven bytes
from the text's UTF-16 unit count. A decoded string retains its text
and Unicode or ANSI type. Re-encoding that value chooses the canonical
prefix and can change the length of the surrounding record.

At a body field, check the unit-count prefix before taking ownership
of the text. Keep the body cursor and field scope at the prior state
if the prefix is overlong. Canonical ANSI source text retains its
original bytes through the Latin-1 representation.
[Exact-build CString evidence](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/CStringArchive2026.md)
[Body text refusal process](../../../../../../tests/Convert/Solidworks/ArchiveValues/ValueRejectTests.py)
