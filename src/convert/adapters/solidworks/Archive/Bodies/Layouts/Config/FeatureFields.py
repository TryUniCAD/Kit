from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Caches.MassCacheFields import (
    KMassCacheFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KFeatureFields = MappingProxyType(
    {
        "moConcept_c.SerializeResolvedData": (
            NativeField(
                "Branch",
                "ctx874",
                BodyValue=(NativeField("Embed", "f60", "moNodeList_c.Serialize"),),
                ModeValue="NotContext",
            ),
        ),
        "moFeature_c.FUN_4bb2b240": (),
        "moFolder_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Scalar", "f360", "i32"),
            NativeField("Scalar", "f370", "i32"),
        ),
        "moModelFeature_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Base", "moFeature_c.FUN_4bb2b240"),
            NativeField("Scalar", "f35c", "i32"),
        ),
        "moMassPropCache_c.Serialize": KMassCacheFields,
        "moSheetMetalMaster_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Length", "n370", "i32", CountValue="f358"),
            NativeField(
                "Branch",
                "n370",
                BodyValue=(
                    NativeField("Fail", "nonempty sheet metal master body list"),
                ),
                ModeValue="NotEquals",
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
