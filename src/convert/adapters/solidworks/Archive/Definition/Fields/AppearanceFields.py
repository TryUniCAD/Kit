from dataclasses import replace as ReplaceValue
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import (
    KObListFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import (
    KGeometryFields as KResolvedGeometry,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# only the measured part manager can introduce concrete appearance bodies
KAppearanceList = NativeField(
    "Branch",
    "",
    BodyValue=(
        NativeField(
            "Mask",
            "part_definition_appearance",
            BodyValue=(NativeField("Embed", "list", "PWMaterialManager_c.materials"),),
            MaskValue=1,
        ),
    ),
    OtherValue=(NativeField("Embed", "list", "suObList"),),
    ModeValue="Expression",
    ExpressionValue=(
        "And",
        ("compare", ("Eq",), ("class_name",), ("literal", "uiPartDoc_c")),
        (
            "compare",
            ("Eq",),
            ("lookup", ("scope",), ("literal", "has_pwmaterial")),
            ("literal", 1),
        ),
    ),
)

# the native manager uses the actual object at every ordered reference
KAppearanceRef = NativeField(
    "Branch",
    "",
    OtherValue=(NativeField("Fail", "invalid Definition appearance reference"),),
    ModeValue="Expression",
    ExpressionValue=(
        "And",
        ("is_node", ("lookup", ("scope",), ("literal", "o"))),
        (
            "compare",
            ("Eq",),
            ("class_of", ("lookup", ("scope",), ("literal", "o"))),
            ("literal", "PWMaterialProperties_c"),
        ),
    ),
)

# classic appearance records need their complete field order independently of visual properties
KAppearanceFields = MappingProxyType(
    {
        "PWMaterialManager_c.materials": (
            ReplaceValue(
                KObListFields[0],
                BodyValue=(*KObListFields[0].BodyValue, KAppearanceRef),
            ),
        ),
        "mgPoint_c.restore": KResolvedGeometry["mgPoint_c.restore"],
        "PWMaterialProperties_c": (
            NativeField(
                "Branch",
                "part_definition_appearance",
                BodyValue=(
                    NativeField(
                        "Fail", "appearance body outside part Definition manager"
                    ),
                ),
                ModeValue="NotContext",
            ),
            *MakeScalarRows("i32", "f20"),
            NativeField(
                "Branch",
                "f20",
                BodyValue=(
                    NativeField("Fail", "unsupported Definition appearance version"),
                ),
                ModeValue="NotEquals",
                MaskValue=1,
            ),
            *MakeScalarRows("u32", "f28 f2c f30"),
            *MakeScalarRows("f64", "f38"),
            *MakeScalarRows("i32", "f40 f48 f4c"),
            *MakeScalarRows("f64", "f68 f70 f78 f80 f88 f90"),
            *MakeScalarRows("i32", "f1c0 f1c4"),
            *MakeScalarRows("f64", "f50 f58"),
            *MakeScalarRows("i32", "f60 f98 f9c"),
            *MakeScalarRows("f64", "fb0 fb8"),
            *MakeScalarRows("i32", "fa0 fa4 fa8"),
            NativeField("Text", "fe0"),
            NativeField("Text", "fe8"),
            *MakeScalarRows("i32", "ff8"),
            *MakeScalarRows("f64", "f100 f108 f110 f118 f120 f128"),
            *MakeScalarRows("u32", "f130"),
            *MakeScalarRows("f64", "f138 f140 f150 f158 f168 f170"),
            *MakeScalarRows("f64", "f178 f180 f188 f190 f198 f1a0"),
            *MakeScalarRows("i32", "f1a8"),
            *MakeScalarRows("f64", "f1d8 f1e0 f1e8 f1f0 f1f8 f200"),
            NativeField("Embed", "f208", "mgPoint_c.restore"),
            *MakeScalarRows("f64", "fc0 fc8"),
            *MakeScalarRows("i32", "f1ac f220"),
            *MakeScalarRows("f64", "f228 f230 f238 f240"),
            *MakeScalarRows("i32", "f248"),
            *MakeScalarRows("f64", "f250 f258 f260 f268 f270 f278"),
            NativeField("Text", "f280"),
            *MakeScalarRows("i32", "fd8 f1b0 f1b4 f1b8 f1bc f288 f2ac"),
            *MakeScalarRows("f64", "f2a0"),
            *MakeScalarRows("i32", "f2a8 f298"),
            *MakeScalarRows("f64", "f1c8"),
            *MakeScalarRows("i32", "f2c0"),
            *MakeScalarRows("f64", "f2c8"),
            *MakeScalarRows("i32", "f2d0"),
            NativeField("Text", "f290"),
            *MakeScalarRows("i32", "f2d4 f2e0 f2e8 f2ec"),
            NativeField("Text", "f2f8"),
            *MakeScalarRows("f64", "f300 f308"),
            *MakeScalarRows("i32", "f310"),
            NativeField("Text", "ff0"),
            *MakeScalarRows("i32", "f314"),
            *MakeScalarRows("f64", "f318"),
        ),
    }
)
