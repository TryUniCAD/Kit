from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.BlockMapFields import (
    KBlockMapFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the two concrete owner suffixes reuse the same feature body and keep embedded records distinct
KOwnerFields = MappingProxyType(
    {
        "moSketchBlockMgr_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Bytes", "f380", MaskValue=16),
            NativeField(
                "Embed", "blocks", "moRefIdToSketchBlockListMap_c.FUN_4c9080f0"
            ),
        ),
        "moRefIdToSketchBlockListMap_c.FUN_4c9080f0": KBlockMapFields,
        "moPrtExplViewManager_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Node", "f358"),
            NativeField("Node", "f360"),
            NativeField("Scalar", "f398", "f64"),
            NativeField("Scalar", "f3a0", "i32"),
            NativeField("Scalar", "f3a4", "i32"),
            NativeField("Embed", "f368", "su_CMapWordToOb.Serialize"),
        ),
        "su_CMapWordToOb.Serialize": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Scalar", "k", "u16"), NativeField("Node", "v")),
                CountValue="n",
            ),
        ),
    }
)
