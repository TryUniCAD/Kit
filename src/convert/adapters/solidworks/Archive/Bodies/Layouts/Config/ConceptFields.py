from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the concrete virtual target keeps the resolved list in the same native feature scope
KConceptFields = MappingProxyType(
    {
        "moConcept_c.SerializeResolvedData": (
            NativeField(
                "Branch",
                "ctx874",
                BodyValue=(NativeField("Embed", "f60", "moNodeList_c.Serialize"),),
                ModeValue="NotContext",
            ),
        ),
        "moNodeList_c.Serialize": (
            NativeField("Embed", "list", "rf.suObList"),
            NativeField("Scalar", "tail", "i32"),
        ),
        "rf.suObList": (
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
