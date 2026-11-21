# Inspect the saved SOLIDWORKS part material assignment

The internal `ReadNamedMat` entry accepts an in-memory ordinary version-19000 part archive. It reports the selected configuration, native catalog and material names, stored material ID and physical density in kg/m³. A matching active directory row, two binary material identities, the physical parameter and a matching material XML association must all agree. [Archive read profile](../../../../../re/solidworks/records/SdkAssignedMaterialRead2026.md)

The profile requires one mapped solid atom, an explicit nonnegative native material ID and empty body and custom override lanes. The result explicitly carries pending appearance and full material XML semantics. Public import, conversion and output admission retain their previous scope.

Eight fresh host processes checked seven hash-pinned assigned saves and the pristine unassigned control. The returned density and catalog/material names match prior SOLIDWORKS 2026 SP05.2 observations. The proof also refuses detached owners, override modes and contradictory XML. [Guarded process receipt](../../../../../re/solidworks/measurements/2026/SdkAssignedMaterialRead01.json)
