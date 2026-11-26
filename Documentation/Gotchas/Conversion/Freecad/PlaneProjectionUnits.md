# FreeCAD plane projection units

A placement base uses millimetres, but FreeCAD evaluates the dot product of its displacement vector and a plane normal as a scalar. Comparing that result with a length quantity invalidates the revolve angle expression on recompute. The cached solid still opens with its expected volume.

Compare the projection with a scalar tolerance expressed in the document's millimetre coordinates. Recompute before measuring the solid, then edit both plane angles, save, reopen, and measure again. [FreeCAD 1.1.3 recompute diagnostic](https://github.com/TryUniCAD/Kit/actions/runs/44760221695/job/136370452400)
