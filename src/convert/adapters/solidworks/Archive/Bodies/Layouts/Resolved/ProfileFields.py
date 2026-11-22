from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KProfileFields = MappingProxyType(
    {
        "FUN_4bb09f20": (
            NativeField("Scalar", "elem", "u32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "alternate FUN_4bb09f20 Branch"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "elem")),
                    ("literal", 0),
                ),
            ),
        ),
        "moOriginProfileFeature_c": (NativeField("Base", "moProfileFeature_c"),),
        "moProfileData.FUN_4bb2ca30": (
            NativeField("Scalar", "f10", "i32"),
            NativeField(
                "Branch",
                "",
                OtherValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Branch",
                                "",
                                BodyValue=(
                                    NativeField(
                                        "Fail",
                                        "alternate moProfileData.FUN_4bb2ca30 Branch",
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
                                        ("literal", 262144),
                                    ),
                                    ("literal", 0),
                                ),
                            ),
                            NativeField(
                                "Branch",
                                "",
                                BodyValue=(
                                    NativeField(
                                        "Embed", "f198", "mo_loadBodyFromArchive"
                                    ),
                                ),
                                ModeValue="Expression",
                                ExpressionValue=(
                                    "Not",
                                    (
                                        "lookup_or",
                                        ("scope",),
                                        ("literal", "transfer"),
                                        ("literal", 0),
                                    ),
                                ),
                            ),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "Not",
                            (
                                "lookup_or",
                                ("context",),
                                ("literal", "ctx874"),
                                ("literal", 0),
                            ),
                        ),
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
                        ("literal", 24576),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Array",
                "f238",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate moProfileData.FUN_4bb2ca30 f238"),
                ),
                CountValue="n238",
                ModeValue="Positive",
            ),
            NativeField("Embed", "f168", "rf.suObArray"),
            NativeField("Embed", "f188", "FUN_4bb09f20"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moProfileData.FUN_4bb2ca30 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "lookup_or",
                        ("lookup_or", ("scope",), ("literal", "f198"), ("mapping", ())),
                        ("literal", "empty"),
                        ("literal", 1),
                    ),
                    ("literal", 0),
                ),
            ),
        ),
        "moProfileData.FUN_4bb2d5c0": (
            NativeField("Scalar", "f2b0", "u32"),
            NativeField(
                "Array",
                "f2a8",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate moProfileData.FUN_4bb2d5c0 f2a8"),
                ),
                CountValue="n2a8",
                ModeValue="Positive",
            ),
        ),
        "moProfileFeature_c": (
            NativeField("Base", "moModelFeature_c"),
            NativeField("Scalar", "f390", "i32"),
            NativeField("Node", "orig_dim_feature", "suObList"),
            NativeField("Scalar", "f3dc", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "alternate moProfileFeature_c Branch"),),
                OtherValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Fail", "moProfileFeature_c condition 0x20 block"
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
                                ("literal", 32),
                            ),
                            ("literal", 0),
                        ),
                    ),
                    NativeField("Node", "pd_f80", "sgSketch"),
                    NativeField("Embed", "d5c0", "moProfileData.FUN_4bb2d5c0"),
                    NativeField("Embed", "ca30", "moProfileData.FUN_4bb2ca30"),
                    NativeField("Base", "moProfileFeature_c.FUN_4bb2d1d0"),
                    NativeField("Node", "f3b8", "sgLineHandle"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField("Fail", "alternate moProfileFeature_c Branch"),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "And",
                            (
                                "Not",
                                (
                                    "select",
                                    (
                                        "compare",
                                        ("Eq",),
                                        ("literal", 32),
                                        ("literal", 0),
                                    ),
                                    (
                                        "compare",
                                        ("Eq",),
                                        (
                                            "lookup_or",
                                            ("context",),
                                            ("literal", "conditions"),
                                            ("literal", 0),
                                        ),
                                        ("literal", 0),
                                    ),
                                    (
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
                                            ("literal", 32),
                                        ),
                                        ("literal", 0),
                                    ),
                                ),
                            ),
                            (
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
                                    ("literal", 1),
                                ),
                                ("literal", 0),
                            ),
                        ),
                    ),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField("Fail", "alternate moProfileFeature_c Branch"),
                        ),
                        OtherValue=(
                            NativeField("Node", "pd_f78"),
                            NativeField("Embed", "pd_ff0", "mgXform_c.restore"),
                            NativeField("Scalar", "pd_has_fe8", "u16"),
                            NativeField(
                                "Branch",
                                "",
                                BodyValue=(
                                    NativeField(
                                        "Fail", "alternate moProfileFeature_c Branch"
                                    ),
                                ),
                                ModeValue="Expression",
                                ExpressionValue=(
                                    "compare",
                                    ("NotEq",),
                                    (
                                        "select",
                                        (
                                            "compare",
                                            ("Gt",),
                                            ("literal", 19000),
                                            ("literal", 340),
                                        ),
                                        (
                                            "lookup",
                                            ("scope",),
                                            ("literal", "pd_has_fe8"),
                                        ),
                                        (
                                            "int",
                                            (
                                                "compare",
                                                ("Gt",),
                                                ("literal", 19000),
                                                ("literal", 322),
                                            ),
                                        ),
                                    ),
                                    ("literal", 0),
                                ),
                            ),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("Eq",),
                            (
                                "lookup_or",
                                ("scope",),
                                ("literal", "write_ref"),
                                ("literal", 1),
                            ),
                            ("literal", 0),
                        ),
                    ),
                    NativeField("Scalar", "pd_f100", "u16"),
                    NativeField("Node", "pd_f110"),
                    NativeField("Scalar", "pd_f11c", "i32"),
                    NativeField("Scalar", "pd_f118", "i32"),
                    NativeField("Scalar", "pd_f2a0", "u32"),
                    NativeField("Scalar", "f3c0", "u16"),
                    NativeField("Node", "f388", "moContourChooser_c"),
                    NativeField("Embed", "pd_f128", "rf.suObArray"),
                    NativeField("Embed", "pd_f148", "rf.suObArray"),
                    NativeField("Scalar", "f42c", "i32"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "f3dc")),
                    ("literal", 0),
                ),
            ),
        ),
        "moProfileFeature_c.FUN_4bb2d1d0": (
            NativeField("Scalar", "f3e0", "u32"),
            NativeField("Embed", "f3e8", "moProfileFeature_c.contours"),
        ),
        "moProfileFeature_c.contours": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(
                    NativeField("Fail", "alternate moProfileFeature_c.contours items"),
                ),
                CountValue="n",
            ),
        ),
        "mo_loadBodyFromArchive": (
            NativeField("Scalar", "empty", "u8"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate mo_loadBodyFromArchive Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    ("lookup_or", ("scope",), ("literal", "empty"), ("literal", 0)),
                    ("literal", 0),
                ),
            ),
        ),
    }
)
