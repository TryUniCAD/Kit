# Closed circular edges can have zero topological vertices

A disclosed ordinary solid cylinder in SOLIDWORKS 2026 SP05.2 returned
`IBody2.GetFaceCount() == 3`, `GetEdgeCount() == 2` and
`GetVertexCount() == 0`. Both circular edges are closed. The curved face and
two caps meet along those edges without B-rep endpoints.

The observer initially required a positive count of every topology class.
It classified the valid zero as missing data and stopped the probe. Model
the expected topology for the admitted analytic profile, check each COM
count, and compare the full topology across the original and generated
lifecycles. The disclosed failure record has SHA-256
`db69dfcbe541884d13a4dbd192b0ab024a03406b6da57fccf9885565e3e7ecc6`.
[Observer correction](../../../../../Changes/Solidworks/Inspection/Profiles/SolidworksCircleBodyTypeObserver.md)
