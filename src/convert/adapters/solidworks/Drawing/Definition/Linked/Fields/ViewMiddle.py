from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# optional view caches need typed framing even when the admitted fresh graph leaves them empty
KViewMiddle = (
    *MakeScalarRows("u16", "f7ac f7bc f7a8 f7c0 f7b0 f7b4 f8ec"),
    NativeField("Scalar", "f8f0", "i32"),
    *(NativeField("Node", FieldName) for FieldName in ("f8f8", "f630", "f640")),
    NativeField(
        "Present",
        "has_f9d8",
        "u16",
        BodyValue=(NativeField("Node", "f9d8"),),
        CountValue="f9d8",
    ),
    NativeField("Scalar", "na10", "u16"),
    NativeField(
        "Branch",
        "na10",
        ModeValue="Nonzero",
        BodyValue=(NativeField("Fail", "drawing view display records"),),
    ),
    *MakeScalarRows("f64", "f9e8 f9f0 f9f8 fa00"),
    *MakeScalarRows("i32", "f610 f614"),
    NativeField("Embed", "f900", "rf.suObArray"),
    NativeField("Embed", "f600", "mgBBox_c.restore"),
    NativeField(
        "Present",
        "has_fb50",
        "u8",
        BodyValue=(NativeField("Embed", "fb50", "viewSketchCache"),),
        CountValue="fb50",
    ),
    NativeField(
        "Array",
        "f858",
        "i32",
        BodyValue=(NativeField("Embed", "vector", "mgVector_c.restore"),),
        CountValue="n860",
    ),
    NativeField("Scalar", "na18", "u16"),
    NativeField(
        "Branch",
        "na18",
        ModeValue="Nonzero",
        BodyValue=(NativeField("Fail", "drawing view detail records"),),
    ),
    NativeField("Scalar", "fb68", "f64"),
    NativeField("Scalar", "fb74", "i32"),
    NativeField("Embed", "fb78", "rf.suObList"),
    NativeField(
        "Present",
        "has_f648",
        "i32",
        BodyValue=(NativeField("Embed", "f648", "mgPoint_c.restore"),),
        CountValue="f648",
    ),
    NativeField("Node", "f658"),
    NativeField("Node", "fb58"),
)
