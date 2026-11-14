# Mass-cache sampling uses local spline poles

## Expectation

A writer could reuse the general `PointOnSurface` evaluator for every Gaussian quadrature point.
That evaluator already returns the correct position and supports rational surfaces.

## Actual behavior

`PointOnSurface` validates and lifts the complete control net for every call.
Mass integration has 64 quadrature points per knot span.
Repeated full-net evaluation therefore grows quadratically as cages acquire more spans.
Reuse would also rebuild the expanded knot vectors for every position and derivative sample.

## Workaround

Validate the complete typed surface once before emission.
Expand each knot vector once before quadrature.
For each sample, select only the local `(degreeU + 1) * (degreeV + 1)` poles and weights.
Evaluate position and both derivatives from the same local basis data.
Rational surfaces use the shared `MassFrame` arithmetic, while ordinary surfaces accumulate their poles directly.
The [local evaluator](../../../../../../src/convert/formats/Fusion/BrepCodec/Journal/Spline/Stencil/SurfacePoint.py) contains the implementation.
The [mass integrator](../../../../../../src/convert/formats/Fusion/DocumentCodec/Form/SurfaceMass.py) hoists expanded knots and reuses this evaluator.
The [native lifecycle](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) confirms that the optimization preserves geometry and mass measurements.
