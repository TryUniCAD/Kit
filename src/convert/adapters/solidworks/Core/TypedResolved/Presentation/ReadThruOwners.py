from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutModes import (
    CheckCutModes,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutBodyLink import (
    ReadCutBodyLink,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckThruScope import (
    CheckThruScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# the presentation extension must consume the same resolved end and selected body ownership as the ordinary semantic reader
def ReadThruOwners(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    RootsValue: tuple[ArchiveNode, ...],
) -> tuple[ExtrudeOwner, ExtrudeOwner]:
    StockValue = ReadExtrude(LinkValue, RootsValue[-3], Features)
    CutValue = ReadExtrude(LinkValue, RootsValue[-1], Features, IsCut=True)
    CheckCutModes(StockValue, CutValue)
    if CutValue.ModeValue != ExtrudeEnd.KThroughAll:
        raise ValueError("presentation extension requires the measured through-all end")
    if (
        StockValue.ProfileValue is not RootsValue[-4]
        or CutValue.ProfileValue is not RootsValue[-2]
    ):
        raise ValueError("presentation operation profiles are not their actual roots")
    Evidence = ReadCutBodyLink(LinkValue, Features, StockValue, CutValue)
    if (
        Evidence.get("binding") != "saved_configuration_atom_alias"
        or Evidence.get("feature_scope_code") != 1
    ):
        raise ValueError("presentation requires the actual saved selected stock")
    CheckThruScope(LinkValue, CutValue)
    DepthValue = StockValue.RequireDepth()
    CheckTreeAlias(
        LinkValue,
        (
            StockValue.EndValue,
            CutValue.EndValue,
            DepthValue.Parameter,
            DepthValue.Dimension,
            DepthValue.HandleValue,
            DepthValue.DisplayValue,
            RequireNative(StockValue.EndValue.FieldsValue.get("f140")),
            RequireNative(CutValue.EndValue.FieldsValue.get("f140")),
        ),
    )
    return StockValue, CutValue
