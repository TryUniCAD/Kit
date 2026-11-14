# Surface area needs its own quadrature resolution

## Expectation

A Gaussian rule that integrates B-spline positions and polynomial moments could also integrate surface area with negligible error.
One quadrature order might therefore serve every mass-cache field.

## Actual behavior

Surface area integrates the square root of a cross-product dot product.
That norm is not a polynomial even when each surface coordinate and derivative is polynomial.
Eight-point quadrature over each knot span left an area error of about `0.0011253 cm²` on Box3.
The native cache contained `28.197749985492635 cm²`, while the asserted current-writer cache contained `28.196624686525613 cm²`.
The other measured geometry still opened, edited, rebuilt, saved, and reopened correctly because Fusion evaluated the actual BRep area.
The [remote failure](https://github.com/TryUniCAD/Kit/actions/runs/43583291958) caught this persisted-cache error in all 11 cases.

## Workaround

Do not infer sufficient area accuracy from exact low-order volume moments.
Use sixteen-point Gaussian quadrature for every knot-span direction and keep the polynomial moment calculations unchanged.
Compare the current writer's stored cache with the native control at `1e-8` absolute and relative tolerance.
Do not relax the tolerance, replace the cache with a native measurement, or discard the area assertion.
The [quadrature rule](../../../../../../src/convert/formats/Fusion/DocumentCodec/Form/IntegrationRules.py) is a mathematical rule, not fitted document data.
The [mass-cache change](../../../../../Changes/Fusion/TSpline/FusionFormMassCache.md) records the resulting acceptance evidence.
