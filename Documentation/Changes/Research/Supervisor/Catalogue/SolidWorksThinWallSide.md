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

The fresh three-recipe replay at local revision
`15a71d161542b49999ea68e9af40e7c1e3faa452` combined the same thin-wall
source with the separate catalogue batching and shutdown patches. On
SOLIDWORKS 34.4.1.1011, the baseline thin wall measured positive local V
from 0 to 2 mm. XY and YZ used native mode 1, XZ used mode 0, and the
midplane control used mode 2 with equal walls on both sides. The worker
verified all 30 archives across the three recipes, including driving edits,
restorations and fresh reopen. Both owned processes exited normally on
the first attempt. All three dependent decoder jobs recorded their
results with unresolved semantic findings. The catalogue result SHA-256 is
`93adfae40b8690e74ed06b3622cbbcefcf1d409e2e79bae0bf24ff96e48b5445`.
[Delivery PR #291](https://github.com/TryUniCAD/Kit/pull/291)
[Thin-wall API finding](../../../../Gotchas/Research/Workers/SolidWorks/ThinExtrudeFrameSide.md)
