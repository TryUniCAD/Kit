# SOLIDWORKS catalogue thin-wall side

The written thin-extrude recipe uses the measured sketch frame to select the
SOLIDWORKS one-sided wall mode. The catalogue requires the wall to extend
toward the positive local profile side. A sketch normal opposite the recipe
basis changes which native mode places the wall on that side. The midplane
mode remains symmetric. The extrusion direction continues to control the
axial depth independently.

Run the existing SOLIDWORKS catalogue authoring command with a fresh output
directory and a written thin-extrude case. The verifier checks the native
wall mode and the independently calculated body bounds, centroid and
volume. It applies the same checks to the saved driving edits, the three
basis planes, and the fresh reopen.
[Catalogue authoring](../../../../Tasks/ResearchCommandLine.md#author-new-catalogue-samples)

The original combined native replay at
`aae8b6498fa7e09e70ea0d1d3369705133ce884e` rejected a written-recipe batch
after both owned processes had exited normally. Its 28 mm by 2 mm thin
profile measured a wall on the negative local side in XY and YZ, with the
correct positive side in XZ. The midplane and volume controls agreed. The
preserved catalogue result SHA-256 is
`1b6e1e6bfbde418c66644f6c73ef698442d76c986e224d953da40ee6a8808c5a`.
A fresh native replay is pending.
[Thin-wall API finding](../../../../Gotchas/Research/Workers/SolidWorks/ThinExtrudeFrameSide.md)
