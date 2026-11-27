# SOLIDWORKS sketch dimension records

The existing neutral reader exposes the P04 rectangle width and height as
driving parameters with ordered point references. It exposes the P02
diameter as a driving parameter bound to the circle. Read the sketch
constraints and follow their parameter IDs to get the name and value in
millimetres. No new reader API is required.

The [byte map](../../../../../re/solidworks/SketchDimensionByteMap.md)
separates the authored dimension bodies from their display links and
distinguishes decoded fields, observed constants and unexplained variation.
The public reader integration tests compare eleven P04 inputs (including four
holdouts) and five P02 inputs with their reopened SOLIDWORKS measurements.

Writer support is unchanged. The dimension bodies have no unexplained
variation in these captures, but the linked display records still have
varying fields without a generation rule. Opening and rebuilding a generated
file in SOLIDWORKS after a driving-dimension edit remains pending.
