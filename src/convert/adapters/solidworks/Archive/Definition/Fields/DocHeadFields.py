from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# document view owners share their exact fields after the native root identity
KDocViewFields: tuple[NativeField, ...] = (
    NativeField("Node", "fac0"),
    *MakeScalarRows("u8", "fac8"),
    NativeField("Embed", "fae8", "mgXform_c.restore"),
    NativeField("Embed", "faf0", "mgXform_c.restore"),
    *MakeScalarRows("u16", "facc fad0"),
    *MakeScalarRows("u8", "fad4"),
    *MakeScalarRows("i32", "fad8_0 fad8_1"),
    NativeField("Node", "fba8"),
    NativeField("Embed", "f878", "apLineStyleMgr_c.Load"),
    NativeField("Node", "f870"),
    NativeField(
        "Array",
        "faf8",
        "u16",
        BodyValue=(NativeField("Node", "o"),),
        CountValue="nenv",
    ),
    NativeField("Embed", "basedoc", "uiBaseDoc_c.Serialize"),
    NativeField("Embed", "fbf0", "uoModelData_c.restore"),
)

# notebook preferences and renderer presence follow the shared document view
KDocHeadPrefix: tuple[NativeField, ...] = (
    *KDocViewFields,
    NativeField("Node", "fb20"),
    *MakeScalarRows("i32", "fb54 fb3c fb40 fd68"),
    *MakeScalarRows("u8", "f850"),
    NativeField("Node", "fab8"),
    *MakeScalarRows("u16", "fb00 fb04"),
    *MakeScalarRows("i32", "fa6c"),
    NativeField("Node", "fa10"),
    *MakeScalarRows("i32", "fa98"),
    NativeField("Embed", "ffd8", "uoNotebookMgr_c.Serialize"),
    *MakeScalarRows("u32", "f1000"),
    *MakeScalarRows("u8", "fa90 f1014"),
    NativeField("Embed", "expand_keys", "su_CStringArray"),
    NativeField("Embed", "expand_vals", "su_CWordArray"),
    *MakeScalarRows("u16", "f7b8"),
    *MakeScalarRows("u8", "has_pwmaterial"),
)

# both renderer paths use the same embedded manager owner after their marker check
KDefRenderer = NativeField("Embed", "f1110", "PWMaterialManager_c.restore")

# the aggregate profile retains the measured classic appearance manager
KDocHeadFields = (
    *KDocHeadPrefix,
    NativeField(
        "Branch",
        "has_pwmaterial",
        BodyValue=(KDefRenderer,),
        ModeValue="Nonzero",
    ),
)
