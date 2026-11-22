from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqSide import (
    ReadEqSide,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# only one enabled part equation with the fixed local division has measured owners
def ReadEqTokens(
    RootValue: ArchiveNode, DepthText: str, WidthText: str
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    Manager = RequireNative(RootValue.FieldsValue.get("f9d0"), "moRelMgr_c").FieldsValue
    Listing = NativeRecord(Manager.get("f58"))
    RowsValue = NativeRows(Listing.get("items"))
    if (
        len(RowsValue) != 1
        or Listing.get("n") != 1
        or Manager.get("f150") != 1
        or Manager.get("f170") != ""
        or Manager.get("f1b0") != -1
        or any(Manager.get(KeyName) != 0 for KeyName in ("f178", "f180", "n1c0"))
        or any(
            not IsLineState(Manager.get(KeyName)) for KeyName in ("f10", "fa0", "f1c0")
        )
    ):
        raise ValueError(
            "local width-depth equation has other relation or external owners"
        )
    Relation = RequireNative(RowsValue[0].get("o"), "moRelation_c")
    RightText = f" = {WidthText} / 2"
    FieldsValue = Relation.FieldsValue
    if (
        FieldsValue.get("f10") != DepthText + RightText
        or FieldsValue.get("f18") != 0x200
        or FieldsValue.get("f38") != "uuUNDEFINED"
        or any(
            FieldsValue.get(KeyName) != 0
            for KeyName in ("f48", "f74", "f88", "f6c", "f8c")
        )
    ):
        raise ValueError(
            "native relation is outside the enabled local width-depth expression"
        )
    (DepthToken,) = ReadEqSide(
        Relation,
        "f58",
        DepthText,
        (("moRelDimension_c", DepthText, 0, 0),),
    )
    RightTokens = ReadEqSide(
        Relation,
        "f60",
        RightText,
        (
            ("moRelOperator_c", "=", 0, 3),
            ("moRelDimension_c", WidthText, 2, 0),
            ("moRelOperator_c", "/", len(WidthText) + 3, 3),
            ("moRelValue_c", "2", len(WidthText) + 5, 2),
        ),
    )
    return Relation, DepthToken, RightTokens[1]
