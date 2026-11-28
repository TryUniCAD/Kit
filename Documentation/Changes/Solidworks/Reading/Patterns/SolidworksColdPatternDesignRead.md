# Preserve cold oblique pattern owners in design-only reads

Use `open_document(source, strict=True, include_brep=False)` to recover the plate, seed, finite hinge, angular datum, linear pattern, live parameters, selected features and analytic body summary without a neutral B-rep. The same typed graph validates both read modes for the supported cache-free single-configuration pattern. The design-only document retains the verified closure and analytic measures in its body summary.

Six regenerated states pass full and design-only reads through both normal path and stream entry points and both neutral JSON round trips. All six retain their exact earlier archive digests. The raw B-rep extraction option continues to report the available stored data. [Exact evidence](../../../../../re/solidworks/measurements/2026/SdkColdPatternDesignRead01.json)
