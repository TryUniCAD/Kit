# Periodic caps must share the mantle axis

A neutral B-rep can pass its topology validation with a circular rim and
cap translated together off the cylinder axis. The references and full
circle trim still close. The local periodic wire reader also requires a
positive signed axial span and an orthonormal frame.

Apply that same span check to both neutral cap stations in wire metres
before admitting the document to the writer. This refuses displaced,
reversed or coincident caps without moving authored geometry. It also
refuses a non-unit axis even when all cap and rim vectors agree.
[Guarded SDK proof](../../../../../../../re/tooling/sw2026/imported_body_source/VerifyPublicCyl.py)
