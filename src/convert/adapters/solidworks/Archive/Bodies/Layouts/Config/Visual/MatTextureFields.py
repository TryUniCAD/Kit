from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current material textures combine thirteen vector values and their distinct trailing fields
KMatTextureFields = (
    *(
        NativeField("Scalar", f"f{OffsetValue:02x}", "f64")
        for OffsetValue in range(8, 0x70, 8)
    ),
    NativeField("Text", "f70"),
    NativeField("Scalar", "f78", "i16"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f80", "f64"),
    NativeField("Scalar", "f88", "f64"),
    NativeField("Scalar", "f9c", "i32"),
)
