from struct import unpack as Unpack

from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckFirstBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinState import (
    CheckThinState,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the saved solid branch has no secondary end displays and does not use surface option words
def CheckWarmEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    Depth = OwnerValue.RequireDepth()
    DimValue, Param, Length = ReadPrismParam(Fields.get("f18"), False)
    DisplayCell = NativeRecord(Depth.DisplayValue.FieldsValue.get("f5b0"))
    DataValue = DisplayCell.get("data")
    if (
        any(
            Fields.get(FieldName) != int(FieldName in ("has_f28", "has_f48"))
            for FieldName in KBlindZeroFields
            if FieldName not in ("f150", "f154")
        )
        or any(type(Fields.get(FieldName)) is not int for FieldName in ("f150", "f154"))
        or Fields.get("f08") != 1
        or Fields.get("f128") != 1
        or Fields.get("f8c") != 0
        or Fields.get("fa0") != 0.0
        or any(
            Fields.get(FieldName) is not None
            for FieldName in ("f20", "fc8", "fd0", "f138", "f90")
        )
        or any(
            not IsLineState(Fields.get(FieldName))
            for FieldName in ("f28", "f48", "fe0", "f100")
        )
        or RequireNative(Fields.get("f140"), "moFromEndSpec_c").FieldsValue != {"t": 0}
        or DimValue is not Depth.Dimension
        or Param is not Depth.Parameter
        or Depth.DepthValue.name != "D1"
        or DisplayCell.get("elem") != 8
        or DisplayCell.get("n") != 1
        or type(DataValue) is not bytes
        or len(DataValue) != 8
        or Unpack("<d", DataValue)[0] != Length
    ):
        raise ValueError(
            "saved chamfer stock has alternate forward blind end ownership"
        )


# earlier stock flags and actual body manager must explain the sole output and its active depth
def CheckWarmStock(
    LinkValue: NativeLink, Owners: ChmfOwners, StockValue: ExtrudeOwner
) -> None:
    CheckFirstBoss(StockValue)
    Fields = StockValue.NodeValue.FieldsValue
    if (
        Fields.get("f28") not in (0x40000140, 0xC0000140)
        or Fields.get("f810") != -1
        or Fields.get("f838") != 0.0
        or Fields.get("f7a0") != 0
        or any(
            not IsLineState(Fields.get(FieldName))
            for FieldName in ("f368", "f388", "f780")
        )
        or any(
            Fields.get(FieldName) is not None
            for FieldName in ("f538", "f548", "f530", "f6e0", "f758")
        )
    ):
        raise ValueError("saved chamfer stock has alternate body scope or modifiers")
    CheckWarmEnd(StockValue)
    CheckThinState(
        StockValue.NodeValue, LinkValue.ConfigValue.RootValue, Owners.AtomValue
    )
