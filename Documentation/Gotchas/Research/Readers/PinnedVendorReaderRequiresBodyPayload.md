# The pinned vendor reader can require a retained body payload

The PR #121 vendor-source reader resolved the original Author04 body from its persisted Parasolid payload. The same strict open refused a cold generated sketch candidate with `SLDPRT contains no readable Parasolid payload`. Its clear parametric inputs still worked through the later strict reader that supports synthesized solids.

Use the pinned source-reader version for the recorded vendor ownership proof and the frozen emitter's reader version for generated strict geometry. Check direct typed stream facts separately where both readers support them. Retain the exact selected revisions and the original refusal for the unsupported endpoint. [Exact-sketch native evidence](../../../../re/solidworks/records/VendorBlindBossExactSketch.md#verified-native-sketch)
