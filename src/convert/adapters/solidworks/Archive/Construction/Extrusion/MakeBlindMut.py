from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndRefs import (
    BlindEndRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.MakeBlindEnd import (
    MakeBlindEnd,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.ExtrusionGraph import (
    ExtrusionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.BindExtrusionMut import (
    BindExtrusionMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionDimMut import (
    MakeExtrusionDimMut,
)
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
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a complete ordinary forward blind boss binds actual profile history and all five native dimension lifetimes before serialization
def MakeBlindMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    ProfileValue: ProfileGraph,
    InputValue: KEndInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    DesignIntent: bool,
    SelectedLeader: int,
) -> ExtrusionGraph:
    if (
        type(ProfileValue) is not ProfileGraph
        or ProfileValue.ProfileValue.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError(
            "blind boss requires its actual generated profile in the owning part"
        )
    FeatureValue = MakeExtrusionNodeMut(
        "moExtrusion_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    DimensionsValue = tuple(
        MakeExtrusionDimMut(
            FeatureValue,
            InputValue,
            OrdinalValue,
            DesignIntent,
            SelectedLeader,
            Allocator,
        )
        for OrdinalValue in (1, 2, 3, 4)
    )
    FromValue = MakeExtrusionDimMut(
        FeatureValue, InputValue, 19, DesignIntent, SelectedLeader, Allocator
    )
    FromEnd = ArchiveNode(
        RuntimeClass("moFromEndSpec_c", 1), {"t": 0, "f28": FromValue.DisplayValue}
    )
    EndValue = MakeBlindEnd(
        InputValue,
        BlindEndRefs(
            DimensionsValue[0].DisplayValue,
            DimensionsValue[1].DisplayValue,
            DimensionsValue[2].DisplayValue,
            DimensionsValue[3].DisplayValue,
            FromEnd,
        ),
    )
    BindExtrusionMut(FeatureValue, ProfileValue, EndValue)
    return ExtrusionGraph(
        FeatureValue, ProfileValue, EndValue, DimensionsValue, FromValue
    )
