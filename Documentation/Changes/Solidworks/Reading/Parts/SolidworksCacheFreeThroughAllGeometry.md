# Cache-free through-all cut geometry

The default SOLIDWORKS 2026 part reader reconstructs the measured circular through-all cuts from a native mid-plane rectangular stock and an owned free circle on a principal plane. A one-direction cut opens on the selected stock cap. A two-direction cut forms a complete tunnel. The neutral feature retains its through-all directions and both absent length slots.

All three disclosed generated parts pass strict path and byte reads with a closed solid. The front-plane part matches the native oracle on volume, area and centre of mass. The top and right cases match their independently frozen analytic predictions. The regression covers the signed rim positions in both cut directions and through both ends.

The [field and geometry record](../../../../../re/solidworks/records/ThroughAllColdGeometryRead2026.md) and [process receipt](../../../../../re/solidworks/measurements/2026/ColdThroughAllGeometryRead01.json) give the exact scope. The cold read is for a circular contour entirely inside one rectangular stock on the same datum.
