from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# saved telemetry gives each start and end record six ordered path and storage tuples
KBioSpanFields = (
    NativeField("Scalar", "f08", "u32"),
    NativeField("Scalar", "f0c", "u32"),
    NativeField("Scalar", "f10", "u32"),
    *(
        FieldValue
        for Index in range(6)
        for FieldValue in (
            NativeField("Text", f"s{Index}"),
            NativeField("Scalar", f"l{Index}", "i32"),
            NativeField("Scalar", f"a{Index}", "u32"),
            NativeField("Scalar", f"b{Index}", "u32"),
        )
    ),
)
