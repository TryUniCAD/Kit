from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.CompFields import (
    KCompGate,
)

# the ordinary drawing helper starts without the separate legacy entity id restore context
KEdgeGate = (
    "And",
    KCompGate,
    (
        "Not",
        (
            "bool",
            ("lookup_or", ("context",), ("literal", "ctx48"), ("literal", 0)),
        ),
    ),
)

# the actual concrete edge vtable uses the complete shared entity reference serializer without a subclass tail
KEdgeFields = MappingProxyType(
    {
        "moEdgeRef_c": (
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Base", "moBEntRef_c"),),
                OtherValue=(
                    NativeField(
                        "Fail", "edge reference special drawing archive context"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=KEdgeGate,
            ),
        ),
    }
)
