from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# parsed tokens must own the exact expression positions and alias their actual side and relation
def ReadEqSide(
    RelationValue: ArchiveNode,
    SideField: str,
    SideText: str,
    TokenSpecs: tuple[tuple[str, str, int, int], ...],
) -> tuple[ArchiveNode, ...]:
    SideValue = RequireNative(
        RelationValue.FieldsValue.get(SideField), "moRelEquationSide_c"
    )
    FieldsValue = SideValue.FieldsValue
    ListValue = NativeRecord(FieldsValue.get("f10"))
    RowsValue = NativeRows(ListValue.get("items"))
    if (
        FieldsValue.get("fa0") is not RelationValue
        or FieldsValue.get("f50") != SideText
        or FieldsValue.get("f58") != 0
        or FieldsValue.get("f98") != int(SideField == "f58")
        or len(RowsValue) != ListValue.get("n")
        or len(RowsValue) != len(TokenSpecs)
    ):
        raise ValueError("local width-depth expression has unqualified parsed sides")
    TokenValues: list[ArchiveNode] = []
    for RowValue, (ClassName, TokenText, StartValue, KindValue) in zip(
        RowsValue, TokenSpecs, strict=True
    ):
        Token = RequireNative(RowValue.get("o"), ClassName)
        TokenFields = Token.FieldsValue
        if (
            TokenFields.get("f08") != TokenText
            or TokenFields.get("f10") != (1 if KindValue == 0 else 8)
            or TokenFields.get("f14") != StartValue
            or TokenFields.get("f18") != StartValue + len(TokenText)
            or TokenFields.get("f1c") != KindValue
        ):
            raise ValueError("local width-depth expression has an unqualified token")
        TokenValues.append(Token)
    return tuple(TokenValues)
