from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.AppearanceFields import (
    KAppearanceList,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# document helpers keep counted collections and preferences in their original native owners
KDocHelperFields = MappingProxyType(
    {
        "uoSketch": (
            NativeField("Scalar", "profile_feature_id", "i32"),
            NativeField("Embed", "f80", "mgXform_c.restore"),
        ),
        "moDimStandard_c": (),
        "moANSI_c": (NativeField("Base", "moDimStandard_c"),),
        "moISO_c": (NativeField("Base", "moDimStandard_c"),),
        "moBS_c": (NativeField("Base", "moDimStandard_c"),),
        "moDIN_c": (NativeField("Base", "moDimStandard_c"),),
        "moJIS_c": (NativeField("Base", "moDimStandard_c"),),
        "moGB_c": (NativeField("Base", "moDimStandard_c"),),
        "moGOST_c": (NativeField("Base", "moDimStandard_c"),),
        "apLineStyleMgr_c.Load": (
            NativeField(
                "Array",
                "styles",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
        ),
        "uiLineFontMgr_c": (
            NativeField(
                "Array",
                "f10",
                "u16",
                BodyValue=(NativeField("Text", "key"), NativeField("Node", "cfg")),
                CountValue="n",
            ),
        ),
        "uoJournal_c": (
            NativeField("Text", "f08"),
            *MakeScalarRows("u32", "f10"),
            *MakeScalarRows("i32", "f18"),
        ),
        "uoNotebookMgr_c.Serialize": (
            NativeField("Node", "f18"),
            NativeField("Embed", "f10", "suObList"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Embed", "f20", "suObList"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Embed", "f30", "suObList"),
            NativeField("Embed", "pending", "suObList"),
        ),
        "uiBaseDoc_c.Serialize": (
            NativeField("Embed", "ole", "DrawingOleItems"),
            NativeField("Scalar", "f2a0", "i32"),
        ),
        "DrawingOleItems": (
            NativeField(
                "Array",
                "f7f8",
                "u32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
        ),
        "PWMaterialManager_c.restore": (
            *MakeScalarRows("i32", "f08 f0c"),
            KAppearanceList,
        ),
        "uoModelData_c.restore": (
            NativeField("Node", "f08"),
            NativeField("Scalar", "f10", "i32"),
        ),
        "su_CWordArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Scalar", "v", "u16"),),
                CountValue="n",
            ),
        ),
        "PVDocSpecificOptionsData_c.Serialize": (
            *MakeScalarRows("i32", "f08 f0c f10 f2c f18 f1c"),
            *MakeScalarRows("u32", "f20"),
            *MakeScalarRows("i32", "f24 f28 f14 f30 f34"),
        ),
    }
)
