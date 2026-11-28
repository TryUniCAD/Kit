# Read native saved circles and radial dimensions

The ordinary SOLIDWORKS 2026 typed reader projects a closed circle from its
actual sketch endpoint and centre indices. The resulting sketch keeps the
existing circle identity, marks the curve as an ordinary closed profile and
preserves its linked radius or diameter constraint. The driving parameter
comes from the actual length parameter. Its optional display cache remains
separately decoded. The fixed-centre constraint refers to the actual sketch
point.

The measured public profile is a single local circle with one driving radius
or diameter and a fixed centre, used by an ordinary forward blind boss.
Other topologies and reversed extrusion semantics retain their existing
reader behavior.

The [saved radial receipt](../../../../re/solidworks/measurements/2026/SdkSavedRadialRead01.json)
binds all twelve exact resolved streams and nine public circle reads. Tests
cover both native-edited dimension modes, their physical archive maps, the
closed contour and both constraint targets.
