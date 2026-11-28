from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# complete view output must retain native collection order and authored identifiers through the final suffix
KViewTail = (
    *(
        NativeField("Embed", FieldName, "rf.suObList")
        for FieldName in ("fa20", "fa68", "fab0", "faf8")
    ),
    NativeField(
        "Branch",
        "f610",
        ModeValue="BitsEqual",
        MaskValue=1,
        CompareValue=1,
        BodyValue=MakeScalarRows("f64", "f878 f880 f888 f890"),
    ),
    NativeField("Scalar", "f8e8", "u8"),
    NativeField("Scalar", "f6b0", "f64"),
    NativeField("Embed", "fc28", "rf.suObList"),
    NativeField("Embed", "fc70", "rf.suObList"),
    NativeField("Scalar", "fd94", "u8"),
    NativeField("Embed", "fcb8", "rf.suObList"),
    *MakeScalarRows("i32", "fe40 fdb8 f410"),
    *MakeScalarRows("f64", "f3e8 f3f0"),
    NativeField(
        "Present",
        "has_fe78",
        "u8",
        BodyValue=(NativeField("Embed", "fe78", "mgPoint_c.restore"),),
        CountValue="fe78",
    ),
    NativeField("Embed", "fd48", "rf.suObList"),
    NativeField("Scalar", "fe8c", "i32"),
    NativeField("Scalar", "fe94", "u32"),
    NativeField(
        "Array",
        "ff48",
        "i32",
        BodyValue=(NativeField("Scalar", "key", "i32"), NativeField("Node", "value")),
        CountValue="nf50",
    ),
    NativeField("Embed", "ff70", "rf.su_CMapObToInt"),
    NativeField(
        "Array",
        "ff60",
        "i32",
        BodyValue=(
            NativeField("Scalar", "key", "i32"),
            NativeField("Scalar", "value", "u32"),
        ),
        CountValue="nf68",
    ),
    *MakeScalarRows("i32", "f540 ffa4 ffa8 ffac f618 ffb4 f558"),
    NativeField("Text", "f548"),
    NativeField("Node", "f1008"),
    NativeField("Text", "f550"),
)
