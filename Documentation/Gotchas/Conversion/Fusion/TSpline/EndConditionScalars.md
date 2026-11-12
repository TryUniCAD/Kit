# TSM edge end conditions are doubles

A record such as `ec 12 0` can look like an edge index plus integer crease flags. The second field is a binary64 end-condition scalar: the native writer loads a double from map-node offset 0x28, and exported `Edge_endCondition` reads the same value.

User crease state is stored separately by namespace 100. Native interior-edge crease/uncrease leaves boundary `ec` records unchanged. Decode the scalar as a float, retain its edge identity and reject nonzero values until their additional behavior is qualified.

[Static field evidence](../../../../../re/Fusion/Reconstruction/TSpline/FieldEvidence.json) and [crease differentials](../../../../../re/Fusion/Reconstruction/TSpline/CreaseInventory.json) establish the distinction.
