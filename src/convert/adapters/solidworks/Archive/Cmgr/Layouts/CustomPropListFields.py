from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# embedded property rows keep their own signed count and wire grammar
KCustomPropListFields = (
    NativeField(
        "Array",
        "items",
        "i32",
        BodyValue=(NativeField("Embed", "p", "moCustomProperty"),),
        CountValue="n",
        ModeValue="Positive",
    ),
)
