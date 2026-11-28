from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.CheckThinDims import (
    CheckThinDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.MakeThinMerid import (
    MakeThinMerid,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinDim import (
    ReadThinDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinSpecs import (
    ReadThinSpecs,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinSweep import (
    ReadThinSweep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)


# the saved radius display can own bytes without becoming a driving wall parameter
def MakeThinOwner(
    LinkValue: NativeLink,
    FeatureValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    NodesValue: tuple[ArchiveNode, ...],
    *,
    IsSaved: bool = False,
) -> ThinRevOwner:
    SweepValue = ReadThinSweep(LinkValue, FeatureValue, Features)
    ModeValue, FirstValue, SecondValue = ReadThinSpecs(FeatureValue, IsSaved=IsSaved)
    SpecValue = RequireNative(FeatureValue.FieldsValue.get("f8f0"), "moThinSpec_c")
    Radial = SpecValue.FieldsValue.get("f48")
    ExtrasValue = (
        () if Radial is None else (ReadThinDim(Radial, "D7", False, IsRadial=True),)
    )
    CheckThinDims(
        NodesValue,
        SweepValue.EndValue.AlongValue,
        FirstValue,
        SecondValue,
        *ExtrasValue,
    )
    Meridian = MakeThinMerid(
        SweepValue.ProfileGraph,
        ModeValue,
        FirstValue.MetresValue,
        SecondValue.MetresValue,
    )
    WallsValue = (
        (FirstValue, SecondValue) if ModeValue == "two_sided" else (FirstValue,)
    )
    return ThinRevOwner(SweepValue, ModeValue, WallsValue, Meridian)
