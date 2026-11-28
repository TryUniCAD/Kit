from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatOnlyField import (
    PatOnlyField,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KMaterialFields = MappingProxyType(
    {
        "moDisplayItem_c.Serialize": (
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "display location and alternate linked object contexts"
                    ),
                ),
                ModeValue="Condition",
                MaskValue=268435457,
            ),
            NativeField("Base", "moDisplayObject_c.FUN_4ba4d3c0"),
            NativeField("Scalar", "f390", "i32"),
            NativeField("Scalar", "f3e0", "i32"),
            NativeField("Embed", "f290", "mgPoint_c.restore"),
            NativeField("Scalar", "has_f298", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f298")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_f288", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f288")),
                    ("literal", 0),
                ),
            ),
            NativeField("Node", "f3f8", "moCompFeature_c"),
            NativeField("Embed", "f400", "mgVector_c.restore"),
            NativeField("Embed", "f2a0", "mgXform_c.restore"),
            NativeField(
                "Array",
                "f2b0",
                "i32",
                BodyValue=(
                    PatOnlyField(
                        NativeField("Scalar", "v", "i32"),
                        "alternate moDisplayItem_c.Serialize f2b0",
                    ),
                ),
                CountValue="n2b0",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "has_f2c0", "u8"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f2c0")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f2c8", "f64"),
            NativeField("Scalar", "has_f2d0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f2d0")),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Array",
                "f3c0",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize f3c0"),
                ),
                CountValue="n3d0",
                ModeValue="Positive",
            ),
            NativeField("Node", "f2d8"),
            NativeField("Scalar", "f3b8", "f64"),
            NativeField(
                "Array",
                "f2e0",
                "u32",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize f2e0"),
                ),
                CountValue="n2e8",
            ),
            NativeField("Scalar", "f2f0", "i32"),
            NativeField("Embed", "f2f8", "utLineWidth_c.Serialize.3.0"),
            NativeField("Scalar", "f2f4", "i32"),
            NativeField("Scalar", "f304", "i32"),
            NativeField("Embed", "f30c", "utLineWidth_c.Serialize.3.0"),
            NativeField("Scalar", "f308", "i32"),
            NativeField("Scalar", "f300", "i32"),
            NativeField("Scalar", "f314", "i32"),
            NativeField("Scalar", "f334", "i32"),
            NativeField("Scalar", "f338", "i32"),
            NativeField("Scalar", "has_f4a0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f4a0")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f318", "i32"),
            NativeField("Scalar", "f31c", "i32"),
            NativeField("Embed", "f320", "utLineWidth_c.Serialize0"),
            NativeField("Scalar", "f328", "i32"),
            NativeField("Scalar", "f32c", "i32"),
            NativeField(
                "Array",
                "f4a8",
                "u32",
                BodyValue=(
                    NativeField("Fail", "alternate moDisplayItem_c.Serialize f4a8"),
                ),
                CountValue="n4a8",
            ),
            NativeField("Scalar", "has_f4b8", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "moWatermarkNoteData_c::Serialize"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f4b8")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "n4f0", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Repeat",
                        "f4f0",
                        BodyValue=(NativeField("Embed", "p", "mgPoint_c.restore"),),
                        CountValue="n4f0",
                        ModeValue="Positive",
                    ),
                    NativeField("Scalar", "n550", "i32"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Repeat",
                                "f550",
                                BodyValue=(
                                    NativeField("Embed", "v", "mgVector_c.restore"),
                                ),
                                CountValue="n550",
                                ModeValue="Positive",
                            ),
                        ),
                        OtherValue=(
                            NativeField("Fail", "moDisplayItem_c vector count >= 3"),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("Lt",),
                            ("lookup", ("scope",), ("literal", "n550")),
                            ("literal", 3),
                        ),
                    ),
                ),
                OtherValue=(NativeField("Fail", "moDisplayItem_c point count >= 5"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Lt",),
                    ("lookup", ("scope",), ("literal", "n4f0")),
                    ("literal", 5),
                ),
            ),
        ),
        "moDisplayObject_c.FUN_4ba4d3c0": (
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "display location and alternate linked object contexts"
                    ),
                ),
                ModeValue="Condition",
                MaskValue=268435457,
            ),
            NativeField("Scalar", "f50", "u16"),
            NativeField("Node", "f30"),
            NativeField("Node", "f40", "moDrView"),
            NativeField("Node", "f48", "moCompRef_c"),
            NativeField("Scalar", "f54", "i32"),
            NativeField("Scalar", "f11c", "i32"),
            NativeField("Embed", "f08", "moEntVisProp_c"),
            NativeField("Embed", "f68", "rf.suObList"),
            NativeField("Embed", "fb0", "rf.suObList"),
            NativeField("Scalar", "f58", "i32"),
            NativeField("Node", "ff8", "moLinkedDispObjArray_c"),
            NativeField("Scalar", "linked", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate moDisplayObject_c.FUN_4ba4d3c0 Branch"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "linked")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f118", "i32"),
        ),
        "moLineViz_c.Serialize.0": (
            NativeField("Text", "f08"),
            NativeField("Embed", "lw", "utLineWidth_c.Serialize.3.0"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f14", "i32"),
        ),
        "utLineWidth_c.Serialize.3.0": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
