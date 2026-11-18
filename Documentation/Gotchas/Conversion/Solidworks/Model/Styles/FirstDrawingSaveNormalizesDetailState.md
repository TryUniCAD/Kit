# The first SOLIDWORKS drawing save normalizes detail state

A generated SOLIDWORKS 2026 SP05.2 drawing and its referenced part can open,
rebuild, save and reopen cleanly with their intended drafting standard,
while their first native saves rewrite detail settings. Both measured
geometries preserve their ISO or ANSI class and selector and their actual
view, part, configuration and origin links.

The same comparison finds 92 changed detail paths in each child and in
each ISO drawing. Both ANSI drawings have one additional change.
SOLIDWORKS sets bit `0x100000` in the drawing detail `f20` flag. The
other changes affect dimension units, Swift settings and exclusion lists.
The exact rewrite sets remain stable over each fresh reopen and edit.

Qualify style retention by comparing the complete typed detail state
before the first native save and after a fresh reopen. The geometry and
drafting-standard checks can pass while that comparison fails.
[Measured pairs](../../../../../../re/solidworks/measurements/2026/DrawingAnsiPairNative01.json)
