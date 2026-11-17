from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.ScalarFields import (
    MakeScalarRows,
)

# the current ui document keeps its own state around the tagged native drawing model
KDocHeadFields: tuple[NativeField, ...] = (
    NativeField("Node", "model"),
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
