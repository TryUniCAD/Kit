from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the thread manager keeps the raw trailing word separate from the native runtime boolean
KThreadFields = MappingProxyType(
    {
        "moCThreadRefMgr_c": (
            NativeField("Length", "n", "i32", CountValue="f18", ModeValue="Positive"),
            NativeField(
                "Repeat",
                "f18",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Length", "m", "u32", CountValue="holders"),
                    NativeField(
                        "Repeat",
                        "holders",
                        BodyValue=(NativeField("Node", "o"),),
                        CountValue="m",
                    ),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
            NativeField("Boolean", "f1a0", "i32"),
        ),
    }
)
