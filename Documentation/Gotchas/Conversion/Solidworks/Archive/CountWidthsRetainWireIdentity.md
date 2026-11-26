# Retain accepted archive count widths

The vendor and framework count stores use the shortest width for a
value. Their readers can also accept escaped forms for values that
fit an earlier width. Decoding the integer and storing it canonically
changes the framing of those records.

Retain the decoded width as a typed field when a body count uses an
accepted longer form. Preserve it while the stored count still describes
the rows. A change in row length uses the canonical writer. The
6-byte form starts with `0xffff` and the 14-byte framework form also uses
the 32-bit marker `0xffffffff`. A vendor count uses that 32-bit word
as its value, so a 14-byte width is invalid in that domain.
[Exact-build count framing](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/MfcCountArchive2026.md)
[Process coverage](../../../../../tests/Convert/Solidworks/ArchiveRows/CountWidthTests.py)
