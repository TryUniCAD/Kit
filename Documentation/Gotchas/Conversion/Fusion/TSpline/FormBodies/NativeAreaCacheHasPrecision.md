# Native Form area caches have their own precision

## Expectation

A difference between an independently integrated area and Fusion's stored area cache must mean that the quadrature order is insufficient.
Raising that order should move the integrated value toward the native one.

## Actual behavior

Eight-point and sixteen-point spans produced the same Box3 area within `1e-13 cm²` and the same HeldPrism5 area within `3.21e-13 cm²`.
Box3 changed from `28.196624686525613` to `28.196624686525713 cm²`.
HeldPrism5 changed from `14.69314686718681` to `14.693146867187131 cm²`.
The measured convergence disproves the quadrature explanation.

The native cache instead embodies its own numerical approximation.
Its relative area gaps are about `3.991e-5` for Box3 and `7.008e-6` for HeldPrism5.
Fusion nevertheless evaluates the expected BRep area and geometry during load, edit, rebuild, export, and reopen.
The [convergence record](../../../../../../re/Fusion/Reconstruction/FormDocuments/General/AreaConvergence.json) binds both remote runs and their exact values.
The [eight-point run](https://github.com/TryUniCAD/Kit/actions/runs/43583291958) and [sixteen-point run](https://github.com/TryUniCAD/Kit/actions/runs/43584701390) both failed an incorrect exact-area assumption.

## Workaround

Compare the current writer's `area` cache with the native mass-cache precision class, `1e-4` relative and `1e-8` absolute tolerance.
Keep volume, center, inertia, and off-diagonal products at `1e-8` absolute and relative tolerance.
Keep exact BRep geometry comparisons at `1e-8` cm in the native lifecycle.
Do not copy a native area value into production or treat its approximation as a mathematical constant.
Retain independent sixteen-point quadrature and its convergence evidence instead of replacing the writer's derived cache.
The [mass-cache change](../../../../../Changes/Fusion/TSpline/FusionFormMassCache.md) distinguishes cache-field precision from exact geometry acceptance.
