from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)


# the two profiles use the same stored count owner with their respective executor modes
def GridRepeat(
    NameValue: str,
    CountName: str,
    BodyValue: tuple[NativeField, ...],
    UseExpression: bool,
) -> NativeField:
    if UseExpression:
        return NativeField(
            "Repeat",
            NameValue,
            BodyValue=BodyValue,
            ModeValue="Expression",
            ExpressionValue=("lookup", ("scope",), ("literal", CountName)),
        )
    return NativeField("Repeat", NameValue, BodyValue=BodyValue, CountValue=CountName)


# splitter columns use the enclosing grid count while retaining their exact cell fields
def SplitterFields(UseExpression: bool) -> tuple[NativeField, ...]:
    Columns = GridRepeat(
        "cols",
        "f0c",
        (
            NativeField("Embed", "xa", "mgXform_c.restore"),
            NativeField("Embed", "xb", "mgXform_c.restore"),
            *MakeScalarRows("u16", "a b"),
            *MakeScalarRows("f64", "c"),
            NativeField("Text", "d"),
        ),
        UseExpression,
    )
    return (
        *MakeScalarRows("u16", "f08 f0c f10 f14 f18 f1c f20 f24"),
        GridRepeat("rows", "f08", (Columns,), UseExpression),
    )


# part and assembly view environments retain both splitters and their actual grid dimensions
KDocEnvironmentFields = MappingProxyType(
    {
        "uiUserModelEnv_c": (
            NativeField("Text", "f08"),
            NativeField("Embed", "f10", "uiSplitterInfo_c.Serialize"),
            *MakeScalarRows("i32", "f1b0 f1b4"),
            NativeField("Embed", "fe0", "uiSplitterInfo_c.Serialize"),
            *MakeScalarRows("i32", "f1b8 f1bc f1c0 f1c4"),
        ),
        "uiSplitterInfo_c.Serialize": SplitterFields(True),
    }
)
