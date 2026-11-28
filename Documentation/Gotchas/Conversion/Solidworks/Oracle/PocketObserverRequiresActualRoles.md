# Pocket observer uses the authored feature names

The native source observer originally required `CurveSketch` and `CurveBoss` in every tree. A generated pocket opened with zero diagnostics and rebuilt, then its observation stopped at the name check. Its actual role names came from the generation request.

Supply the generated part's declared feature names to the observer. Keep the presence, suppression, rebuild and feature-order checks active for those names. [Pocket edit observer](../../../../Changes/Solidworks/Inspection/Cohorts/Cut/SolidworksBlindPocketEditMeasurement.md)
