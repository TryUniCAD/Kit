# FreeCAD origin cylinder source deck

Task `B04-SW2026-FREECAD-CYLINDER`, PR #121. FreeCAD 1.1.4 authored two disclosed full cylinders at the origin with positive radius and height. Strict Kit decoding preserved the unique body, the actual producing feature and its typed `Radius` and `Height` properties. Both are feature-owned driving millimetre lengths. The neutral projection records their actual IDs and editable roles.

The geometric check uses volume `πr²h`, surface area `2πr(r + h)` and centre `(0, 0, h/2)`. Both disclosed FreeCAD solids have three faces and agree with all three independent predictions.

The native source deck requests an ordinary radius-driven Front Plane circle with fixed centre and forward blind depth. It carries each independent driver edit and custody information for the original FCStd and its strict neutral projection. Native source authoring, fresh reopen, first-writer locks, FreeCAD lowering and generated-output validation remain tracked by this workstream. Partial sweeps, translated or rotated primitives, and additive cylinder attachments have their own unqualified source conditions.

To replay the preparation, supply the disclosed author report, its original FCStd inputs and their strict neutral JSON projections in the source directory. Use an unused output path and the exact author report hash from the receipt. [Disclosed receipt](../measurements/2026/FreecadCylinderSourceDeck01.json) [Preparation tool](../../tooling/sw2026/freecad_cylinder/PrepareSourceDeck.py)
