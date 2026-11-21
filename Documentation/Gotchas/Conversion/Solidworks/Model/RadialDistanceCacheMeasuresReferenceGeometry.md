# Radial distance cache measures reference geometry

The persisted common-display `fad0` field must not be initialized by unconditionally copying a radius or diameter parameter.

On the pinned SOLIDWORKS 2026 SP05.2 ordinary local circle path, common engine `0x4c8a0a40` calls helper `[0x4c8413a0,0x4c84153f)` and stores its result at `0x4c8a1305`. The helper compares actual first/second reference points. For a retained 2D `sgCircleDim` with null optional transforms/views, these are the circle center transformed through the inverse profile frame, and zero. If their difference passes native `IsNotNull`, the helper returns its Euclidean norm; otherwise it returns the dimension parameter value. The actual direction callback is false on this class.

An origin-centered circle can therefore make this cache appear to be a direct parameter copy while an off-origin circle exercises a different native branch. Keep the reference geometry, frame, component threshold and parameter fallback explicit. No captured field value is a default.

The complete original function SHA-256 is `80ade3060a00f6832dcf3721fb4cc3e1501299e0b9e4e312bca1ab50cad16acc` under model image SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The [independent proof](../../../../../re/solidworks/records/RadialEngineConstruction2026.json) and [field ledger](../../../../../re/solidworks/records/RadialEngineFieldRules2026.json) retain this boundary. Static construction ownership does not establish fresh native acceptance or later callback preservation.
