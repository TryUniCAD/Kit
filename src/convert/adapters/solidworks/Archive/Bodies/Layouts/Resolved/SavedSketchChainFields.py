from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the saved resolved body reaches these ordinary native owner fields in their verified order
KSavedSketchChainFields = MappingProxyType(
    {
        "moSketchChain_c": (
            NativeField("Embed", "f08", "su_CDWordArray"),
            NativeField("Embed", "f60", "su_CDWordArray"),
            NativeField("Scalar", "f28", "u32"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f50", "i32"),
            NativeField("Scalar", "f54", "i32"),
            NativeField("Scalar", "f58", "u32"),
            NativeField("Scalar", "f5c", "u32"),
            NativeField("Text", "f80"),
            NativeField("Scalar", "flags", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "moSketchChain_c flags >= 4 throw"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("GtE",),
                    ("lookup", ("scope",), ("literal", "flags")),
                    ("literal", 4),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Node", "f30", "sg3DPlaneHandle"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        ("lookup", ("scope",), ("literal", "flags")),
                        ("literal", 1),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Node", "f40", "sgPointHandle"),
                    NativeField("Node", "f48", "sgPointHandle"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        ("lookup", ("scope",), ("literal", "flags")),
                        ("literal", 2),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "fd0", "u32"),
            NativeField(
                "Array",
                "end_map",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "k", "u32"),
                    NativeField("Scalar", "v", "u32"),
                ),
                CountValue="nmap",
                ModeValue="Positive",
            ),
            NativeField("Node", "fc0", "contourTrimData_c"),
            NativeField("Node", "fc8", "contourTrimData_c"),
            NativeField("Scalar", "f90", "i32"),
            NativeField("Scalar", "fa0", "i32"),
            NativeField("Scalar", "fa4", "i32"),
        ),
    }
)
