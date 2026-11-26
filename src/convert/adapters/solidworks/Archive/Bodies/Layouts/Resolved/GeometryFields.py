from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KGeometryFields = MappingProxyType(
    {
        "mgPoint_c.operator>>": (
            NativeField("Scalar", "x", "f64"),
            NativeField("Scalar", "y", "f64"),
            NativeField("Scalar", "z", "f64"),
        ),
        "mgPoint_c.restore": (
            NativeField("Scalar", "x", "f64"),
            NativeField("Scalar", "y", "f64"),
            NativeField("Scalar", "z", "f64"),
        ),
        "mgPoint_c.restore2D": (
            NativeField("Scalar", "x", "f64"),
            NativeField("Scalar", "y", "f64"),
        ),
        "mgXform_c.operator>>": (
            NativeField(
                "Repeat",
                "words",
                BodyValue=(NativeField("Scalar", "w", "u32"),),
                ModeValue="Fixed",
                MaskValue=30,
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate mgXform_c.operator>> Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "BitAnd",
                        (
                            "lookup",
                            (
                                "lookup",
                                ("lookup", ("scope",), ("literal", "words")),
                                ("literal", 28),
                            ),
                            ("literal", "w"),
                        ),
                        ("literal", 240),
                    ),
                    ("literal", 16),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate mgXform_c.operator>> Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "BitAnd",
                        (
                            "lookup",
                            (
                                "lookup",
                                ("lookup", ("scope",), ("literal", "words")),
                                ("literal", 28),
                            ),
                            ("literal", "w"),
                        ),
                        ("literal", 240),
                    ),
                    ("literal", 32),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate mgXform_c.operator>> Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "BitAnd",
                        (
                            "lookup",
                            (
                                "lookup",
                                ("lookup", ("scope",), ("literal", "words")),
                                ("literal", 28),
                            ),
                            ("literal", "w"),
                        ),
                        ("literal", 240),
                    ),
                    ("literal", 64),
                ),
            ),
        ),
    }
)
