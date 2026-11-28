# Inspect the saved SOLIDWORKS part material assignment

The internal `ReadNamedMat` entry accepts an in-memory ordinary version-19000 part archive. It reports the selected configuration, native catalog and material names, stored material ID and physical density in kg/m³. A matching active directory row, two binary material identities, the physical parameter and a matching material XML association must all agree. [Archive read profile](../../../../../re/solidworks/records/SdkAssignedMaterialRead2026.md)

The profile requires one mapped solid atom, an explicit nonnegative native material ID and empty body and custom override lanes. The result explicitly carries pending appearance and full material XML semantics.

Eight fresh host processes checked seven hash-pinned assigned saves and the pristine unassigned control. The returned density and catalog/material names match prior SOLIDWORKS 2026 SP05.2 observations. The proof also refuses detached owners, override modes and contradictory XML. [Guarded process receipt](../../../../../re/solidworks/measurements/2026/SdkAssignedMaterialRead01.json)

The public reader now joins the active native partition atom and producing
feature to the selected design body. The body's `material_id` references a
portable record with the verified name and density. The color stays unset.
Native publication refuses unresolved physical assignment or appearance
before staging. Sixteen guarded workers compare the actual seven saved
parts and unassigned control in both strict read modes with the prior SDK.
[Public readback proof](../../../../../re/solidworks/measurements/2026/SdkAssignedPartMaterialAggregate01.json)
