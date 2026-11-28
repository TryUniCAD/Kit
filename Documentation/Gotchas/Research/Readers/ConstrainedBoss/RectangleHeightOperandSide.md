# Rectangle height operand side

A width, height and Origin check can agree even when a writer selects the wrong edge for the height driver. The saved SOLIDWORKS P03 Front-plane baseline measures height from the origin along the left edge. The current dimensioned rectangle stage in PR #121 selects the right edge for its Front-plane height driver. Both lengths are 20 mm. They reference different point pairs.

Read the relation's ordered endpoint selectors and match them to the selected contour and Origin. Preserve the source's left edge and operand direction in the logical input. Treat four inferred corner joins as identities of shared points. Do not write four additional saved solver relations.

The [source intent process case](../../../../Changes/Research/Encoder/ConstrainedBossIntent.md) checks both anchored sizes. It substitutes the opposite edge at the same length and reverses the original height operands in separate refusals. [PR #121 constructor](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Archive/Construction/SketchDimensions/ReadRectEdges.py)
