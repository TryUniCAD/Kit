from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevCore import (
    ReadRevCore,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# each operation retains its selected endpoints and the cutter can reverse independently of both full stocks
def ReadRevCutOps(
    LinkValue: NativeLink, Features: dict[int, ArchiveNode]
) -> tuple[RevolveOwner, RevolveOwner, RevolveOwner]:
    FirstProfile, FirstNode, SecondProfile, SecondNode, CutProfile, CutNode = tuple(
        Features.values()
    )[-6:]
    Nodes = (FirstNode, SecondNode, CutNode)
    Profiles = (FirstProfile, SecondProfile, CutProfile)
    if tuple(ReadParents(Value) for Value in Nodes) != tuple(
        (Value,) for Value in Profiles
    ):
        raise ValueError(
            "selected revolve cut operation lacks its actual sole archive profile"
        )
    First = ReadRevCore(LinkValue, FirstNode, FirstProfile, Features, 1)
    Second = ReadRevCore(LinkValue, SecondNode, SecondProfile, Features, 0)
    CutValue = ReadRevCore(LinkValue, CutNode, CutProfile, Features, 1)
    Owners = (First, Second, CutValue)
    FrameValue = First.FrameValue
    _ = ReadPrincAxis(FrameValue.SupportValue)
    NodesToBind = tuple(
        Value
        for Owner in Owners
        for Value in (
            Owner.NodeValue,
            Owner.ProfileValue,
            Owner.SketchValue,
            Owner.AxisValue.WrapperValue,
            Owner.AxisValue.SelectionValue,
            Owner.AxisValue.HandleValue,
            Owner.AngleValue.DisplayValue,
            Owner.AngleValue.HandleValue,
            Owner.AngleValue.DimensionValue,
            Owner.AngleValue.ParameterValue,
        )
    )
    if (
        len(set(NodesToBind)) != len(NodesToBind)
        or First.IsReverse
        or Second.IsReverse
        or any(
            Owner.FrameValue.SupportValue != FrameValue.SupportValue
            or Owner.FrameValue.StartValue != FrameValue.StartValue
            or Owner.FrameValue.EndValue != FrameValue.EndValue
            or Owner.AngleValue.NameValue != "D1"
            or Owner.EndValue.ModeValue != "one_sided"
            or Owner.ProfileGraph.EqualValue is not None
            for Owner in Owners
        )
        or First.AngleValue.RadiansValue != FullTurn
        or Second.AngleValue.RadiansValue != FullTurn
        or not (0 < CutValue.AngleValue.RadiansValue < FullTurn)
    ):
        raise ValueError(
            "selected revolve cut requires independent D1 owners, coaxial full stocks and a partial cut"
        )
    CheckTreeAlias(LinkValue, NodesToBind)
    return Owners
