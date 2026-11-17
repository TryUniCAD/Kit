from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# part and assembly view environments retain both splitters and their actual grid dimensions
KDocEnvironmentFields = MappingProxyType(
    {
        "uiUserModelEnv_c": (
            NativeField("Text", "f08"),
            NativeField("Embed", "f10", "uiSplitterInfo_c.Serialize"),
            *MakeScalarRows("i32", "f1b0 f1b4"),
            NativeField("Embed", "fe0", "uiSplitterInfo_c.Serialize"),
            *MakeScalarRows("i32", "f1b8 f1bc f1c0 f1c4"),
        ),
        "uiSplitterInfo_c.Serialize": (
            *MakeScalarRows("u16", "f08 f0c f10 f14 f18 f1c f20 f24"),
            NativeField(
                "Repeat",
                "rows",
                BodyValue=(
                    NativeField(
                        "Repeat",
                        "cols",
                        BodyValue=(
                            NativeField("Embed", "xa", "mgXform_c.restore"),
                            NativeField("Embed", "xb", "mgXform_c.restore"),
                            *MakeScalarRows("u16", "a b"),
                            *MakeScalarRows("f64", "c"),
                            NativeField("Text", "d"),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=("lookup", ("scope",), ("literal", "f0c")),
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=("lookup", ("scope",), ("literal", "f08")),
            ),
        ),
    }
)
