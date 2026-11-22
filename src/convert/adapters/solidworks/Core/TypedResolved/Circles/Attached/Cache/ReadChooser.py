from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckCacheFace import (
    CheckCacheFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# cap history may store the retired blind length but cannot introduce active selections or operators
def ReadChooser(
    RowValue: Mapping[str, object], BossValue: ArchiveNode, ArcMark: int
) -> tuple[tuple[tuple[ArchiveNode, ArchiveNode, ArchiveNode], ...], ArchiveNode]:
    ItemValue = RequireNative(RowValue.get("o"), "moPerBodyChooserData_c").FieldsValue
    Faces = NativeRecord(ItemValue.get("f08"))
    Bounds = NativeRecord(ItemValue.get("f48"))
    Flags = NativeRecord(ItemValue.get("f78"))
    if (
        not IsLineState(ItemValue.get("f28"))
        or any(ItemValue.get(NameValue) != 0 for NameValue in ("f68", "f6c", "f70"))
        or (Faces.get("n"), Bounds.get("n"), Flags.get("n")) != (2, 1, 1)
        or NativeRows(Flags.get("items")) != ({"v": 0},)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser carries additional selection state"
        )
    FacesValue = tuple(
        CheckCacheFace(
            RequireNative(RowValue.get("o"), "moFaceRef_c"),
            BossValue,
            CapValue,
            ArcMark,
        )
        for CapValue, RowValue in zip(
            range(2), NativeRows(Faces.get("items")), strict=True
        )
    )
    (BoundsRow,) = NativeRows(Bounds.get("items"))
    return FacesValue, RequireNative(BoundsRow.get("o"), "moBBoxCenterData_c")
