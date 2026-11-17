# A mate can correct placement before an explicit rebuild

The first `IComponent2.Transform2` read after opening a SOLIDWORKS assembly can already contain a solved placement. In the measured version-19000 aligned coincident mate, the typed archive and both endpoint frames placed the floating occurrence `0.00473 m` off-plane. The first native observation had zero plane offset. The fixed anchor stayed in place.

Compare the typed stored transforms and reference frames with the first post-open observation before calling `ForceRebuild3`. Record both native poses and the original open status. The generated assembly and two native A17 brackets passed with zero open errors and warnings. The read-only run kept the original files intact. [Native receipt](../../../../../re/solidworks/measurements/2026/GeneratedCoincidentMateActiveSolve01.json)
