from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# faceted support references retain their snapshot metadata through an independent counted body
KFacetFields = (
    NativeField(
        "Present",
        "has_points",
        "u16",
        BodyValue=(
            NativeField(
                "Array",
                "f08",
                "i32",
                BodyValue=(NativeField("Embed", "p", "mgPoint_c.restore"),),
                CountValue="f10",
                ModeValue="Positive",
            ),
        ),
    ),
    *(
        NativeField("Scalar", NameValue, "i32")
        for NameValue in ("f40", "f44", "f48", "f4c", "f14", "f50", "f54")
    ),
    NativeField("Scalar", "f58_empty", "i32"),
    NativeField(
        "Branch",
        "f58_empty",
        OtherValue=(NativeField("Text", "f58"),),
        ModeValue="Nonzero",
    ),
)
