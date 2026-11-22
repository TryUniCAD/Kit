# Sweep section seam can rotate on edit

## Expectation

The saved seam of a fixed-centre sweep section circle remains on its originally authored sketch axis when D1 changes.

## Actual behavior

Both disclosed SOLIDWORKS 2026 SP05.2 section edits preserve the shared endpoint, exact circle centre and editable diameter while rotating the local seam to approximately 17 degrees. Both original saves and the independent path-radius edits retain the original zero phase. The Parasolid section plane and circle retain their own frame throughout. [Exact section observations](../../../../../re/solidworks/measurements/2026/OrdinarySweptBossArchive01.json)

## Workaround

Resolve the actual sketch end and centre indices. Verify the aliased end point and its radial distance independently of its angle. Preserve the observed seam when retaining a saved sketch. Treat the native seam producer as a separate construction rule. [Archive and driver evidence](../../../../../re/solidworks/records/OrdinarySweptBossArchive2026.md)
