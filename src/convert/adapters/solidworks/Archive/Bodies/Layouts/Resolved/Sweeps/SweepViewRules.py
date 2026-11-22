from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# radial display nodes share the existing parameter owner and native base display fields
KSweepViewRules = MappingProxyType(
    {
        "moFtrFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Node", "f388", "moFtrFolder_c"),
            NativeField("Scalar", "f37c", "i32"),
            NativeField("Scalar", "f394", "i32"),
            NativeField(
                "Virtual",
                "",
                BodyValue=(NativeField("Scalar", "f378", "i32"),),
                ModeValue="Flag",
                MaskValue=2624,
            ),
            NativeField("Scalar", "f39c", "i32"),
        ),
        "moDisplayRadialDim_c": (
            NativeField("Base", "moDisplayDim_c.FUN_4c82c3d0"),
            NativeField("Scalar", "ffd8", "i32"),
            NativeField("Scalar", "ffe0", "f64"),
            NativeField("Scalar", "ffe8", "f64"),
            NativeField("Scalar", "fff0", "f64"),
            NativeField("Scalar", "fff8", "f64"),
            NativeField("Scalar", "f1000", "f64"),
            NativeField("Scalar", "f1008", "f64"),
            NativeField("Embed", "f1010", "mgPoint_c.restore"),
            NativeField("Embed", "f1028", "mgPoint_c.restore"),
            NativeField(
                "Array",
                "ffc0",
                "i32",
                BodyValue=(NativeField("Text", "s"),),
                CountValue="nfc0",
                ModeValue="Positive",
            ),
            NativeField("Node", "f1050", "moHwCalloutData_c"),
            NativeField("Text", "f1048"),
            NativeField("Node", "f1068", "suObList"),
            NativeField("Scalar", "has_f1060", "i32"),
            NativeField(
                "Branch",
                "has_f1060",
                BodyValue=(NativeField("Embed", "f1060", "mgXform_c.restore"),),
                ModeValue="Nonzero",
            ),
            NativeField("Node", "f1090", "moMirrorHWHelper_c"),
            NativeField("Scalar", "ffd4", "i32"),
            NativeField("Node", "f10a8", "moHoleWizardInfo_c"),
            NativeField("Scalar", "f10a4", "i32"),
        ),
        "moSkDimHandle_c.Serialize": (
            NativeField("Base", "moDimHandle_c.FUN_4c82a810"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "moSkDimHandle_c condition 1 vtable 0x778"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "And",
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
                    (
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
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Scalar", "dim_type", "u16"),),
                        OtherValue=(NativeField("Node", "ff0", "sgSketch"),),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("IsNot",),
                            (
                                "lookup_or",
                                ("scope",),
                                ("literal", "fe8"),
                                ("literal", None),
                            ),
                            ("literal", None),
                        ),
                    ),
                    NativeField("Scalar", "ff8", "i32"),
                ),
                OtherValue=(
                    NativeField("Scalar", "ff0", "i32"),
                    NativeField("Scalar", "ff8", "i32"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "And",
                    (
                        "Not",
                        (
                            "select",
                            ("compare", ("Eq",), ("literal", 6), ("literal", 0)),
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
                                    ("literal", 6),
                                ),
                                ("literal", 0),
                            ),
                        ),
                    ),
                    (
                        "Or",
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
                        (
                            "bool",
                            (
                                "lookup_or",
                                ("context",),
                                ("literal", "ctx874"),
                                ("literal", 0),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        "moSkDimHandleRadial_c": (NativeField("Base", "moSkDimHandle_c.Serialize"),),
    }
)
