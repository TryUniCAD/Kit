from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the current relation owner keeps its separate cache and nullable member rows
KRelMgrFields = MappingProxyType(
    {
        "RelCacheDimValueMap_c.Serialize": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(
                    NativeField("Text", "k"),
                    NativeField("Scalar", "v", "f64"),
                ),
                CountValue="n",
            ),
        ),
        "moRelMgr_c": (
            NativeField("Embed", "f58", "suObList"),
            NativeField("Embed", "f10", "RelCacheDimValueMap_c.Serialize"),
            NativeField("Text", "f170"),
            NativeField("Scalar", "f178", "i32"),
            NativeField("Scalar", "f180", "u32"),
            NativeField("Scalar", "f150", "i32"),
            NativeField("Scalar", "ff4", "i32"),
            NativeField("Embed", "fa0", "suObList"),
            NativeField("Scalar", "f1b0", "i32"),
            NativeField("Length", "n1c0", "u32", CountValue="f1c0"),
            NativeField(
                "Repeat",
                "f1c0",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n1c0",
            ),
        ),
    }
)
