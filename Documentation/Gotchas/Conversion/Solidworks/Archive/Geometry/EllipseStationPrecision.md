# Translated ellipse stations round before the public conic is recovered

SOLIDWORKS stores the centre and the two principal stations as absolute
binary64 model coordinates. Adding each signed radial offset to a translated
centre and subtracting it after reading changes the offset within the error
of those operations. A fixed dot-product tolerance rejected an ordinary
40 × 30 mm ellipse centred at (70, 70) mm and rotated 33 degrees. The exact
signed station geometry had roundoff comparable to the recovered dot product.

The cold reader bounds that error from the independently stored component
ULPs. It still checks the signed axes, the separate major-station seam, the
reflected endpoints and every clear stream. Recreating the physical minor
station from the displayed radii and angle loses one or two ULPs even for the
two disclosed measured parts. Preserve their actual typed geometric stations
in the neutral sketch and verify that they project to its same public conic.
Both write routes then regenerate from those coordinates and require exact
strict document equality before publication.

[Scoped ellipse review evidence](../../../../../../re/solidworks/records/SdkColdEllipsePromotion2026.md)
