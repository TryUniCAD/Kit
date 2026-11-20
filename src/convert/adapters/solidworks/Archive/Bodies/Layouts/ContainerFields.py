from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the native object array keeps its count word and uses the shared object map for its rows
KContainerFields = MappingProxyType(
    {
        "su_CObArray": (
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
