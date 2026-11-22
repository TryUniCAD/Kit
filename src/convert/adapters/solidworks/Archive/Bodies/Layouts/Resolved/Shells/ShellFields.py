from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RecordFields import (
    KRecordFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current saved shell fields separate the removed caps and the auxiliary edge
KShellFields = MappingProxyType(
    {
        "moPartConfiguration_c.SerializeMBSMDataObjects": (
            NativeField(
                "Array",
                "fcd8",
                "u32",
                BodyValue=(
                    NativeField("Fail", "alternate saved shell inline body map"),
                ),
                CountValue="n",
            ),
        ),
        "moShell_c": (
            NativeField("Base", "moBodyFeature_c"),
            NativeField("Node", "f828", "suObList"),
            NativeField("Node", "f818", "moDisplayDim_c"),
            NativeField("Scalar", "f820", "u8"),
            NativeField("Node", "f830", "suObList"),
            NativeField("Node", "f838", "suObList"),
            NativeField("Node", "f848", "moCompEdge_c"),
            NativeField("Node", "f850", "moCompSolidBody_c"),
        ),
        "moFaceRef_c": (
            NativeField("Base", "moBEntRef_c"),
            NativeField(
                "Branch",
                "",
                OtherValue=(
                    NativeField(
                        "Array",
                        "ff0",
                        "i32",
                        BodyValue=(
                            NativeField("Fail", "alternate shell multiple matches"),
                        ),
                        CountValue="nf0",
                        ModeValue="Positive",
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        (
                            "lookup_or",
                            ("context",),
                            ("literal", "conditions"),
                            ("literal", 0),
                        ),
                        ("literal", 128),
                    ),
                    ("literal", 0),
                ),
            ),
        ),
        "ThreeDRadiusDim_c": (NativeField("Base", "moFeatureDim_c.FUN_4c833f00"),),
        "moPMarkRecord_c": KRecordFields["moPMarkRecord_c"],
    }
)
