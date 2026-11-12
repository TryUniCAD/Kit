# OGS entity identities use explicit big-endian bytes

Most OGS fixed-width values are little endian. Applying that rule to `EntityID` or `ACTEntityID` consumes the expected eight bytes but produces an unrelated entity identity.

Native node-data serialization constructs an eight-byte array by shifting the identity and writes it through the byte-array primitive. The resulting numeric order is big endian. Segment IDs remain ordinary little-endian uint32 values.

Decode the two identity fields with their explicit order and resolve the resulting segment/object pair against the document graph. The [binary facts](../../../../../re/Fusion/Reconstruction/OgsScene/BinaryFacts.json) record the native shifts and literal addresses; the [wire model](../../../../../re/Fusion/Reconstruction/OgsScene/WireModel.md) distinguishes these from float64 qualifiers and serialization IDs.
