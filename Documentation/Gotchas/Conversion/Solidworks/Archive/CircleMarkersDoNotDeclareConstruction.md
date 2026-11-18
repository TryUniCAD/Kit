# Circle markers do not declare construction geometry

The legacy sketch marker scan returned a solid-driving circle as a construction
entity after a native edit and reopen. It also used an unbound generic distance.
The active native sketch retains the same ordinary contour, typed radial
dimension and local centre point.

Follow the typed arc and check its entity `f54` bit 0 and registered contour
state `fd0`. Equal endpoint indices encode a closed circle. Follow the
radial handle to the actual value dimension and the fixed relation to its
centre point. Use legacy markers to retain the existing neutral entity identity.
[Exact saved comparisons](../../../../../re/solidworks/measurements/2026/SdkSavedRadialRead01.json)
