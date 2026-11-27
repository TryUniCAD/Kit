# A no-op save can shift centre-of-mass readback by one ULP

Two successive warmed saves of an unchanged SOLIDWORKS 2026 SP04.1 polygon boss used the same path and title. The native Z centre-of-mass observation moved from `0x1.458cd20afa2efp-7` to `0x1.458cd20afa2f0p-7` metres. The driving dimension, other geometry measurements and presentation observations were equal. An exact whole-observation comparison stopped the original run before the requested setting change.

Keep the raw measurements. Use the existing native geometry tolerances for the numerical comparisons and exact comparisons for feature ownership, driver values and the presentation observations. [Native observation](../../../../../../re/solidworks/measurements/2026/VendorBossCorpus/PlaneVisibilityContrast.json)
