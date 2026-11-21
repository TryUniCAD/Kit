# Cylinder child spheres use the box diagonal

A cylinder's minimum physical bounding sphere has radius `sqrt(r*r + (depth/2)**2)`. Using that radius for the ordinary child `mgBBox_c` silently changes its native sphere state. The pinned box setter computes the midpoint of the two axis-aligned corners and half the full three-dimensional box diagonal, which includes both radial widths.

Six disclosed cylinder child saves preserve that box sphere in their occurrence-local caches. Compute the fresh local box from the actual circle/profile/end owners, apply the confirmed point-pair rule, then preserve its sphere independently through placement and parent union. Do not tighten it to a minimum cylinder sphere or recompute it from a rotated aggregate box.

The D03 low-y kernel extrema differ by one ULP from direct `cy-r`; retain that measured limit without a fitted adjustment. This does not qualify a native circular assembly writer.

[Native edges, exact comparisons and source-only process proof](../../../../../../re/solidworks/records/CircleChildBounds2026.md)
