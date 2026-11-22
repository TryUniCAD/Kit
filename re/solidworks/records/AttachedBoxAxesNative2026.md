# Attached FreeCAD box with three native reference axes

SOLIDWORKS 2026 SP05.2 opened, rebuilt and saved the disclosed intact F14c
candidate with a signed rectangular box and three selectable reference axes.
Both controls passed. Four separate application processes reported executable
build `34.5.2.0604`, x64 and SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
The macOS agent started each operation through the Windows 11 Parallels guest.
Windows Python 3.12.7 ARM64 used the registered SOLIDWORKS COM server.

The exact 10,707-byte candidate has SHA-256
`0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc`.
The guarded build read zero runtime input files. Native rebuild preserved a
fully constrained sketch, the reversed blind boss and one solid with eight
vertices, twelve edges and six faces. The initial volume was 6,000 mm³,
area 2,200 mm² and centre of mass (10, −5, 15) mm.

The observer independently edited the length to 27 mm, width to 37 mm and
height to 15 mm. A fresh application process reopened the four resulting
files with zero open errors and warnings. Body geometry and the complete
native tree matched in all states. The axes kept positive X, Y and Z
directions through the origin and the two actual datum-plane parents.
The generated phase recorded 336 numerical checks and the reopen phase
recorded 192 checks. The original candidate remained immutable.
[Native receipt](../measurements/2026/AttachedBoxAxesNative01.json)

The first invocation stopped before launching SOLIDWORKS when isolated
Python hid the installed COM binding. The successful trial used the
registered binding with a fresh output directory and the exact same
candidate and pristine control. Public source publication remains an
independent requirement. This disclosed trial earns zero held-out and
corpus-conversion credits.
[Committed observer](../../tooling/sw2026/attached_top_box_source/ObserveAttachedBoxAxes.py)
[Evidence verifier](../../tooling/sw2026/attached_top_box_source/SummarizeAttachedBoxAxes.py)
