from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.CheckStockMode import (
    CheckStockMode,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude


# each physical stock must keep its own preceding profile and editable depth
def ReadStockOps(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    *,
    AllowSavedTolerance: bool = False,
) -> tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner]:
    FirstProfile, FirstNode, SecondProfile, SecondNode, CutProfile, CutNode = tuple(
        Features.values()
    )[-6:]
    FirstStock = ReadExtrude(LinkValue, FirstNode, Features)
    SecondStock = ReadExtrude(LinkValue, SecondNode, Features, NewSolid=True)
    CutValue = ReadExtrude(LinkValue, CutNode, Features, IsCut=True)
    CheckStockMode(FirstStock, FirstProfile, -1)
    CheckStockMode(
        SecondStock, SecondProfile, 0, AllowSavedTolerance=AllowSavedTolerance
    )
    CheckStockMode(CutValue, CutProfile, 1)
    FirstDepth, SecondDepth = FirstStock.RequireDepth(), SecondStock.RequireDepth()
    if (
        FirstDepth.Parameter is SecondDepth.Parameter
        or FirstDepth.Dimension is SecondDepth.Dimension
        or FirstDepth.Dimension.FieldsValue["f50"]
        == SecondDepth.Dimension.FieldsValue["f50"]
        or FirstDepth.HandleValue is SecondDepth.HandleValue
        or FirstDepth.DisplayValue is SecondDepth.DisplayValue
    ):
        raise ValueError("independent stocks share an actual driving depth owner")
    return FirstStock, SecondStock, CutValue
