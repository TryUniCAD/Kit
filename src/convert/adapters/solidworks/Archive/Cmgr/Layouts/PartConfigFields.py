from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# part configuration fields extend the shared configuration while retaining their own body states
KPartConfigFields = (
    NativeField("Base", "moBaseConfiguration_c"),
    NativeField("Embed", "f4d0", "moPartConfigObject_c"),
    NativeField("Scalar", "fc50", "f64"),
    NativeField("Node", "fc48"),
    NativeField("Scalar", "fc60", "i32"),
    NativeField("Context", "conditions", ModeValue="Set", MaskValue=512),
    NativeField(
        "Array",
        "fca8",
        "i32",
        BodyValue=(
            NativeField("Node", "body"),
            NativeField("Scalar", "state", "i32"),
            NativeField("Node", "vis"),
        ),
        CountValue="nca8",
        ModeValue="Positive",
    ),
    NativeField("Context", "conditions", ModeValue="Clear", MaskValue=512),
    NativeField(
        "Branch",
        "",
        BodyValue=(
            NativeField("Node", "fcb8"),
            NativeField("Node", "fcc0"),
        ),
        ModeValue="NotCondition",
        MaskValue=1,
    ),
    NativeField(
        "Branch",
        "",
        BodyValue=(NativeField("Scalar", "fcc8", "u32"),),
        ModeValue="NotCondition",
        MaskValue=1,
    ),
    NativeField("Scalar", "fccc", "i32"),
    NativeField(
        "Array",
        "fce8",
        "i32",
        BodyValue=(
            NativeField("Scalar", "a", "i32"),
            NativeField("Scalar", "b", "i32"),
        ),
        CountValue="nce8",
        ModeValue="Positive",
    ),
    NativeField(
        "Array",
        "fd20",
        "u32",
        BodyValue=(
            NativeField("Scalar", "a", "i32"),
            NativeField("Scalar", "b", "i32"),
        ),
        CountValue="nd20",
    ),
    NativeField("Scalar", "fc64", "i32"),
    NativeField("Scalar", "fcd4", "i32"),
    NativeField("Scalar", "fcd0", "i32"),
    NativeField(
        "Array",
        "fdc8",
        "Split",
        BodyValue=(NativeField("Scalar", "v", "i32"),),
        CountValue="ndc8_hi",
        OtherName="ndc8_lo",
    ),
)
