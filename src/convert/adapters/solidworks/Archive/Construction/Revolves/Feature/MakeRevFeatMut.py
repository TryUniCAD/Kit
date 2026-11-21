from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevAngleMut import (
    MakeRevAngleMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevAxisRef import (
    MakeRevAxisRef,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevEnd import (
    MakeRevEnd,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevNodeMut import (
    MakeRevNodeMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeThinSpecMut import (
    MakeThinSpecMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the ordinary boss must retain its profile construction axis and each active angular display in the same fresh model
def MakeRevFeatMut(
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    AxisValue: ArchiveNode,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
    *,
    IsThin: bool = False,
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode, DimensionGraph]:
    WallsValue = PlanValue.ThinWalls
    IsThin = IsThin or WallsValue is not None
    FeatureValue = MakeRevNodeMut(
        PlanValue.FeatureName,
        SystemValue.RootValue,
        InputValue.TargetValue,
        Allocator,
        IsThin=IsThin,
    )
    Reference = MakeRevAxisRef(SystemValue, ProfileValue, AxisValue, PlanValue)
    AngleValue = MakeRevAngleMut(FeatureValue, InputValue, PlanValue, Allocator)
    AgainstValue = (
        None
        if PlanValue.AgainstAngle is None
        else MakeRevAngleMut(
            FeatureValue, InputValue, PlanValue, Allocator, Against=True
        )
    )
    EndValue = MakeRevEnd(FeatureValue, AngleValue, PlanValue.SideMode, AgainstValue)
    FeatureValue.FieldsValue.update(
        {
            "f60": {
                "list": {"n": 1, "items": [{"o": ProfileValue.ProfileValue}]},
                "tail": 0,
            },
            "f808": None,
            "f824": int(PlanValue.IsReverse),
            "f810": None,
            "f820": 0,
            "f818": ArchiveNode(RuntimeClass("suObList", 1), {"n": 0, "items": []}),
            "f828": 5 if IsThin else 3,
            "f870": 1,
            "f830": Reference,
            "f8d8": EndValue,
            "f8e8": 0,
        }
    )
    if WallsValue is not None:
        FeatureValue.FieldsValue["f8f0"] = MakeThinSpecMut(
            FeatureValue, InputValue, Allocator, ProfileValue.FrameValue, PlanValue, WallsValue
        )
    return FeatureValue, Reference, EndValue, AngleValue
