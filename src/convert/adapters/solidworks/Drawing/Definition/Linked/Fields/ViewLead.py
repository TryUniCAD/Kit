from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# view support objects must inherit the surrounding native archive condition and actual feature ownership
KViewLead = (
    NativeField("Embed", "fd28", "rf.suObArray"),
    NativeField("Base", "moModelFeature_c"),
    *(
        NativeField("Embed", FieldName, "mgXform_c.restore")
        for FieldName in ("f5e0", "f6b8", "f6c0")
    ),
    *MakeScalarRows("f64", "f6d8 f6e0 f6e8 f6f0 f718 f720 f728 f730"),
    NativeField("Embed", "f778", "mgPoint_c.restore"),
    *MakeScalarRows("f64", "f780 f788"),
    NativeField("Scalar", "f798", "u8"),
    NativeField(
        "Branch",
        "f798",
        ModeValue="Nonzero",
        BodyValue=(
            NativeField("Embed", "f5e8", "mgXform_c.restore"),
            NativeField("Embed", "f5f0", "mgXform_c.restore"),
        ),
    ),
    NativeField("Scalar", "f79c", "u8"),
    NativeField("Text", "fe30_name"),
    NativeField("Scalar", "fe30_flags", "i32"),
    NativeField(
        "Present",
        "has_f6c8",
        "u8",
        BodyValue=(
            NativeField("Node", "f6c8"),
            NativeField("Embed", "f6d0", "mgVector_c.restore"),
        ),
        CountValue="f6c8",
    ),
    *(
        NativeField(
            "Present",
            "has_" + FieldName,
            "u8",
            BodyValue=(NativeField("Node", FieldName),),
            CountValue=FieldName,
        )
        for FieldName in ("f7c8", "f8e0", "fde0")
    ),
    NativeField("Node", "f5d8"),
    NativeField("Node", "f968"),
)
