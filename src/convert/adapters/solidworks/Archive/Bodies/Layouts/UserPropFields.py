from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the native property list preserves each stored scalar kind and its original field width
KUserPropFields = (
    NativeField(
        "Array",
        "props",
        "i32",
        BodyValue=(
            NativeField("Scalar", "kind", "u32"),
            NativeField(
                "Branch",
                "kind",
                BodyValue=(NativeField("Fail", "user property kind"),),
                ModeValue="Greater",
                MaskValue=2,
            ),
            NativeField(
                "Branch",
                "kind",
                BodyValue=(NativeField("Scalar", "v", "f32"),),
                ModeValue="Equals",
            ),
            NativeField(
                "Branch",
                "kind",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                ModeValue="Equals",
                MaskValue=1,
            ),
            NativeField(
                "Branch",
                "kind",
                BodyValue=(NativeField("Text", "v"),),
                ModeValue="Equals",
                MaskValue=2,
            ),
        ),
        CountValue="n",
        ModeValue="Positive",
    ),
)
