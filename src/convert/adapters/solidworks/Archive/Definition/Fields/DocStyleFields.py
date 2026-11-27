from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# populated saved documents need their actual style segments and bill of materials owners
KDocStyleFields = MappingProxyType(
    {
        "moLineStyle_c": (
            NativeField("Text", "f08"),
            NativeField("Text", "f10"),
            NativeField(
                "Array",
                "f18",
                "u16",
                BodyValue=(NativeField("Scalar", "seg", "f64"),),
                CountValue="nseg",
            ),
            NativeField("Scalar", "f20", "u8"),
        ),
        "moBomInfoMgr_c": (
            NativeField(
                "Array",
                "f08",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
        ),
    }
)
