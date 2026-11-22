from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the local equation links its value token to the native rectangle dimension handle and pointer graph
KWidthDimLayouts = MappingProxyType(
    {
        "moSkDimHandleValG2_c": (NativeField("Base", "moSkDimHandle_c.Serialize"),),
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
        "sgPntPntDist": (NativeField("Base", "sk.sgValG2Dim.FUN_4c59f080"),),
        "sk.sgValDim.FUN_4c59ea80": (
            NativeField("Base", "sk.sgDim.FUN_4c5868d0"),
            NativeField("Scalar", "fa0", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "xform", "mgXform_c.operator>>"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "fa0")),
                    ("literal", 0),
                ),
            ),
        ),
        "sk.sgValG2Dim.FUN_4c59f080": (
            NativeField("Base", "sk.sgValDim.FUN_4c59ea80"),
            NativeField("Node", "h1", "sgEntHandle"),
            NativeField("Node", "h2", "sgEntHandle"),
            NativeField("Scalar", "f180", "u16"),
            NativeField("Scalar", "f184", "u16"),
            NativeField("Scalar", "f1b8", "u16"),
            NativeField("Scalar", "f1bc", "u16"),
            NativeField("Node", "plane", "sg3DPlaneHandle"),
            NativeField("Embed", "dir", "mgVector_c.restore"),
        ),
    }
)


# only physically observed schema one dimension and external origin classes are added to the ordinary graphs
KWidthDimSchemas = {
    "moCompSketchEntHandle_c": (1,),
    "moPointBackedUpData_c": (1,),
    "moSkDimHandleValG2_c": (1,),
    "moSketchExtRef_w": (1,),
    "sgExtEnt_c": (1,),
    "sgPntPntDist": (1,),
}
