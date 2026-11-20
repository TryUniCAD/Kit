from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# embedded and tagged object lists share the vendor count and object field grammar
KObListFields = (
    NativeField(
        "Array",
        "items",
        "Count",
        BodyValue=(NativeField("Node", "o"),),
        CountValue="n",
    ),
)
