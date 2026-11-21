from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# empty color owners still store the raw word before interpreting the signed count
KFeatColorFields = (
    NativeField("Length", "n", "u32", CountValue="items"),
    NativeField(
        "Repeat",
        "items",
        BodyValue=(
            NativeField("Embed", "vp", "moVisualProperties_c.restore"),
            NativeField("Scalar", "v", "i32"),
        ),
        CountValue="n",
        ModeValue="SignedPositive",
    ),
)
