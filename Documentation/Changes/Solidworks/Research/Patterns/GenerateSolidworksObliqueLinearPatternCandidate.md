# Generate a bounded oblique SOLIDWORKS linear pattern candidate

Kit's research tools can construct a standalone part with a plate, merged raised seed, actual hinge and angular direction plane, and a one-direction linear feature pattern with editable count and pitch. The two demonstrated geometries have independent dimensions, counts, signed directions and placement. The internal tooling generates a complete cold container from the supplied model and shared archive rules.

Both disclosed containers opened and rebuilt in SOLIDWORKS 2026 SP05.2 with
zero errors and warnings. Each returned one solid with the predicted mass
properties, selected seed and datum, and editable count and pitch. The
native dependency list also included the base plate. The source requires
only the seed and the selected direction datum, so this comparison remains
unqualified. [Model construction](../../../../../re/solidworks/records/LocalLinearPatternContainer2026.md) ·
[Native comparison](../../../../../re/solidworks/measurements/2026/GeneratedObliquePatternNative01.json)
