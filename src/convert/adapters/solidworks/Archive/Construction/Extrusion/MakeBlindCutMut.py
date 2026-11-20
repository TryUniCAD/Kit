from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndParam import (
    ReadEndParam,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.BindExtrusionMut import (
    BindExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionDimMut import (
    MakeEndDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionNodeMut import (
    MakeExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a reversed blind cut owns one live depth and rebuilds its affected body information
def MakeBlindCutMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    ProfileValue: ProfileGraph,
    InputValue: BossEndInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    DesignIntent: bool,
    SelectedLeader: int,
) -> CutGraph:
    if (
        type(CastValue(object, InputValue)) is not BossEndInput
        or InputValue.ModeValue != "blind"
        or not InputValue.IsReversed
    ):
        raise ValueError("ordinary cut requires its single reversed blind depth")
    if (
        type(ProfileValue) is not ProfileGraph
        or type(ProfileValue.GeometryValue) is not CircleGraph
        or ProfileValue.ProfileValue.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError("ordinary cut requires its actual circular profile")
    FeatureValue = MakeExtrudeMut(
        "moICE_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    DepthValue = MakeEndDimMut(
        FeatureValue, InputValue, 1, DesignIntent, SelectedLeader, Allocator
    )
    _ = ReadEndParam(InputValue, DepthValue.DisplayValue, 1)
    FromEndValue = ArchiveNode(RuntimeClass("moFromEndSpec_c", 1), {"t": 0})
    EndValue = MakeEndSpec(
        "blind", True, DepthValue.DisplayValue, None, None, None, FromEndValue
    )
    BindExtrudeMut(FeatureValue, ProfileValue, EndValue)
    return CutGraph(FeatureValue, ProfileValue, EndValue, DepthValue)
