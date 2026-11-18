from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.BindExtrusionMut import (
    BindExtrusionMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionNodeMut import (
    MakeExtrusionNodeMut,
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
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughEnd import (
    MakeThroughEnd,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary resolved circular cuts share the real native cut feature allocation and profile ownership without allocating a depth identity
def MakeThruCutMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    ProfileValue: ProfileGraph,
    InputValue: ThroughEndInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> CutGraph:
    if type(InputValue) is not ThroughEndInput:
        raise TypeError("through all cut requires its typed end input")
    if (
        type(ProfileValue) is not ProfileGraph
        or type(ProfileValue.GeometryValue) is not CircleGraph
        or ProfileValue.ProfileValue.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError("through all cut requires its actual owned circular profile")
    FeatureValue = MakeExtrusionNodeMut(
        "moICE_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    EndValue = MakeThroughEnd(InputValue)
    BindExtrusionMut(FeatureValue, ProfileValue, EndValue)
    return CutGraph(FeatureValue, ProfileValue, EndValue, None)
