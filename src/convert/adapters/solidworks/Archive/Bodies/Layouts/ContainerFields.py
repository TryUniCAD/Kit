from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# archive containers share exact count framing while retaining each native row type
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
        "su_CDWordArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Scalar", "v", "u32"),),
                CountValue="n",
            ),
        ),
        "su_CStringArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Text", "s"),),
                CountValue="n",
            ),
        ),
    }
)
