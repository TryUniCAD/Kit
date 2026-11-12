# Graphics class names do not imply object handles

The expectation that every named OGS object has a shared resource handle is false. Serializer constructors independently select the resource flag. `PrimitiveLODGeometryNode` clears it and writes its node-data selector immediately after the class name. `SimpleMesh`, `VertexBuffer` and `CircleArc<double>` retain it and write a resource identity before their fields. A repeated resource writes its class/identity link without duplicating its definition.

The ordinary primitive LOD also differs from `SerializeForBody`: it writes a general mesh link and omits the body-specific display-item discriminator. Generic `SimpleMesh` uses shared vertex resources and six float32 model bounds; its LOD world bounds are six float64 values. Fusion's `OgsSimpleMesh` is a different serializer with an inline vertex-buffer payload and a planarity flag.

Use class-specific typed dispatch and preserve the three framing decisions independently. Do not infer identities from names or reuse a similarly named body serializer. [Installed native instruction evidence](../../../../../re/Fusion/Reconstruction/OgsScene/PrimitiveLodEvidence.json) and [whole-document acceptance](../../../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json) establish these distinctions for the three circular controls.
