from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KCoreFields = MappingProxyType(
    {
        "moNode_c": (
            NativeField("Virtual", "", MaskValue=1208),
            NativeField("Virtual", "", MaskValue=1216),
        ),
        "rf.suObArray.ResultAtoms": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Node", "o", "moAtom_c"),),
                CountValue="n",
            ),
        ),
        "rf.suObArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Fail", "alternate rf.suObArray items"),),
                CountValue="n",
            ),
        ),
    }
)
