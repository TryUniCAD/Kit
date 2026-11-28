from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KCoreFields = MappingProxyType(
    {
        "moNode_c": (
            NativeField("Virtual", "", MaskValue=1208),
            NativeField("Virtual", "", MaskValue=1216),
        ),
        "moPartConfiguration_c.SerializeMBSMDataObjects": (
            NativeField(
                "Array",
                "fcd8",
                "u32",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Node", "o"),
                ),
                CountValue="n",
            ),
        ),
        "rf.suObArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
        ),
    }
)
