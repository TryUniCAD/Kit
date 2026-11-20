# Directional light names can repeat

On the measured SOLIDWORKS 2026 SP05.2 part, `GetLightSourceCount`
returned four light slots. `GetLightSourceName` returned
`Ambient-1` at index zero and `Directional-1` at each of the
other three indices. String uniqueness refused that scene before
any edit.

Use the numeric light positions for these native operations. Check
the count again after each deletion and bind the saved scene
through the actual tagged objects. Names alone do not distinguish
the directional owners.
