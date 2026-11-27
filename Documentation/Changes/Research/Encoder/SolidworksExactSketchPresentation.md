# SOLIDWORKS exact sketch and presentation

One research request can generate a straight-line blind boss with exact SI geometry, millimetre display units, one default Top annotation, and a document-wide construction-plane setting. The existing stand-alone request formats remain strict. [Request and replay guide](../../../../re/solidworks/records/VendorBlindBossExactSketchPresentation.md)

Fresh source-free processes reproduced the same combined archive and verified both Boolean settings. Toggling construction planes changed one byte in the Definition stream. Both candidates retained the exact sketch and D1, signed Top frame, and the same directed solid. Five unsupported requests failed before output. Native application behaviour for these combined candidates remains unmeasured. [Offline evidence](../../../../re/solidworks/measurements/2026/VendorBlindBossExactSketchPresentation.json)

A third source-free replay used the captured `Default` configuration name. The strict SDK, typed configuration directory and keyword row all returned that name. The five name-bearing streams changed, while the paired Top, plane and solid results stayed the same. The source and generated MMGS formatting still differ. [Captured-name replay](../../../../re/solidworks/records/VendorBlindBossExactSketchPresentation.md#replay-the-captured-configuration-name)
