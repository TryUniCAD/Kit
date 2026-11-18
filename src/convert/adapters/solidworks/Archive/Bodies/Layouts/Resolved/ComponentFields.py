from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KComponentFields = MappingProxyType(
    {
        "moCompFeature_c": (
            NativeField("Base", "moCompRef_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Scalar", "cond_fr", "i32"),),
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
                                ("literal", 65536),
                            ),
                            ("literal", 0),
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
                        ("literal", 1),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "ff0", "moFRData_c"),),
                OtherValue=(
                    NativeField("Scalar", "has_ff0", "i32"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Embed", "ff0", "moFRData_c"),),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("NotEq",),
                            ("lookup", ("scope",), ("literal", "has_ff0")),
                            ("literal", 0),
                        ),
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "select",
                    (
                        "compare",
                        ("NotEq",),
                        (
                            "lookup_or",
                            ("scope",),
                            ("literal", "cond_fr"),
                            ("literal", 0),
                        ),
                        ("literal", 0),
                    ),
                    ("literal", True),
                    (
                        "select",
                        (
                            "Not",
                            (
                                "select",
                                ("compare", ("Eq",), ("literal", 1), ("literal", 0)),
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
                                        ("literal", 1),
                                    ),
                                    ("literal", 0),
                                ),
                            ),
                        ),
                        ("literal", True),
                        (
                            "select",
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
                                    ("literal", 2097152),
                                ),
                                ("literal", 0),
                            ),
                            ("literal", True),
                            (
                                "bool",
                                (
                                    "Or",
                                    (
                                        "lookup_or",
                                        ("context",),
                                        ("literal", "ctx874"),
                                        ("literal", 0),
                                    ),
                                    (
                                        "lookup_or",
                                        ("context",),
                                        ("literal", "ctx894"),
                                        ("literal", 0),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        "moCompRefPlane_c": (
            NativeField("Base", "moCompFeature_c"),
            NativeField("Node", "ff8", "moRefGeom_c"),
            NativeField("Scalar", "f100", "i32"),
        ),
        "moCompRef_c": (
            NativeField("Node", "f58", "moComponent_c"),
            NativeField("Scalar", "f68", "i32"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f1c", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f30", "i32"),
            NativeField("Scalar", "f70", "i32"),
            NativeField("Scalar", "f84", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "f88", "moOldRef_c"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "f84")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "fa0", "i32"),
            NativeField("Scalar", "f34", "u32"),
            NativeField("Scalar", "f48", "i32"),
            NativeField("Scalar", "f90", "i32"),
            NativeField("Scalar", "f94", "i32"),
            NativeField("Scalar", "f98", "i32"),
            NativeField("Scalar", "f9c", "i32"),
            NativeField("Scalar", "has_fb0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Node", "fb0", "moFacetedData_c"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_fb0")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_fb8", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Text", "fb8"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_fb8")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_fc0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "fc0", "moCompRefInfo_c"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_fc0")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_fc8", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "fc8", "mgXform_c.restore"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_fc8")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_fd0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Text", "fd0"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_fd0")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f4c", "u32"),
        ),
        "moFRData_c": (
            NativeField("Scalar", "f00", "i32"),
            NativeField("Scalar", "f08", "u32"),
        ),
        "moCompSolidBody_c": (
            NativeField("Base", "moCompRef_c"),
            NativeField("Node", "ff0", "moFaceRef_c"),
            NativeField("Scalar", "n110", "i32"),
            NativeField(
                "Repeat",
                "f110",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                CountValue="n110",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "f108", "i32"),
            NativeField("Scalar", "f104", "i32"),
            NativeField("Scalar", "f100", "i32"),
        ),
        "moHistoryFeatItemData_c": (
            NativeField("Base", "moNode_c"),
            NativeField("Node", "f48", "moCompFeature_c"),
        ),
    }
)
