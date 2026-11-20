from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KViewFields = MappingProxyType(
    {
        "moView_c": (
            NativeField("Text", "f358"),
            NativeField("Embed", "f368", "mgXform_c.restore"),
            NativeField("Embed", "f370", "mgXform_c.restore"),
            NativeField("Scalar", "f388", "u16"),
            NativeField("Scalar", "f38c", "i32"),
            NativeField("Scalar", "f378", "f64"),
            NativeField(
                "Array",
                "f380",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n380",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "f360", "i32"),
            NativeField(
                "Branch",
                "ctx3d0",
                BodyValue=(
                    NativeField(
                        "Context", "conditions", ModeValue="Set", MaskValue=512
                    ),
                ),
                ModeValue="Context",
            ),
            NativeField("Context", "ctx87c", ModeValue="Assign", MaskValue=1),
            NativeField("Scalar", "f394", "i32"),
            NativeField("Scalar", "n398", "i32"),
            NativeField(
                "Branch",
                "n398",
                BodyValue=(NativeField("Embed", "f398", "suObList"),),
                ModeValue="NotEquals",
            ),
            NativeField("Context", "ctx87c", ModeValue="Assign"),
            NativeField("Context", "ctx87c", ModeValue="Assign", MaskValue=1),
            NativeField("Scalar", "f3a8", "i32"),
            NativeField("Scalar", "f3b8", "f64"),
            NativeField("Scalar", "n3b0", "i32"),
            NativeField(
                "Branch",
                "n3b0",
                BodyValue=(NativeField("Embed", "f3b0", "suObList"),),
                ModeValue="NotEquals",
            ),
            NativeField("Context", "ctx87c", ModeValue="Assign"),
            NativeField(
                "Branch",
                "ctx3d0",
                BodyValue=(
                    NativeField(
                        "Context", "conditions", ModeValue="Clear", MaskValue=512
                    ),
                ),
                ModeValue="Context",
            ),
            NativeField("Scalar", "f3c0", "i32"),
            NativeField("Scalar", "f3c8", "i32"),
        ),
    }
)
