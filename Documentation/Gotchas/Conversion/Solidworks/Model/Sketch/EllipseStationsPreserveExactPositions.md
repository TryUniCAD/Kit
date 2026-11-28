# A normalized ellipse can round its minor station

The cold reader recovers the radius and unit major direction from the
actual typed axis stations. Projecting those rounded values back onto the
conic can move the minor station by one or more binary64 steps. Both
disclosed signed ellipse profiles reproduce their centre and major
position through that round trip and lose exact minor position.

Retain the actual centre, major and minor metre pairs in the cold neutral
projection. Verify that these positions produce the same neutral conic,
then regenerate the seam, opposed stations and archive owners using the
existing constructor. The entire output and complete strict source
projection must match before publication.
[Guarded exact comparison](../../../../../../re/solidworks/records/SdkColdEllipseRepublication2026.md)
