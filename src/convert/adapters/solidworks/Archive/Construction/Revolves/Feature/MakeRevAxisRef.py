from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the selected line must retain actual component profile creation time index and permanent identity instead of only cached axis coordinates
def MakeRevAxisRef(
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    AxisValue: ArchiveNode,
    PlanValue: RevolvePlan,
) -> ArchiveNode:
    Geometry = RequirePolygon(ProfileValue.GeometryValue)
    if (
        ProfileValue.ProfileValue.FieldsValue.get("owner") is not SystemValue.RootValue
        or Geometry.LineValues[-1] is not AxisValue
    ):
        raise ValueError(
            "revolve axis reference requires its actual generated local profile and line"
        )
    Component = ArchiveNode.RequireNode(SystemValue.RootValue.FieldsValue["f990"])
    FieldsValue = CompRefFields(Component)
    FieldsValue.update(
        {
            "ff0": {
                "f00": FieldInt(ProfileValue.ProfileValue.FieldsValue, "f08"),
                "f08": 2592000,
            },
            "f0f8": MakeLineHandle(
                Geometry.SketchValue, AxisValue, len(Geometry.LineValues) - 1
            ),
            "f100": FieldInt(AxisValue.FieldsValue, "f08"),
        }
    )
    SelectedValue = ArchiveNode(RuntimeClass("moCompSketchEntHandle_c", 1), FieldsValue)
    return ArchiveNode(
        RuntimeClass("moLineRef_w", 1),
        {
            "f58": SelectedValue,
            "f60": None,
            "f68": 0,
            "f6c": 0,
            "f08": 101,
            "has_f10": 0,
            "has_f18": 0,
            "f0c": -1,
            "f20": 0,
            "f74": -12345,
            "f78": -12345,
            "f7c": -12345,
            "f50": 0,
            "f70": 19000,
            "f34": 0,
            "f30": 0,
            "f98": 0,
            "f38": -1,
            "fc8": {"x": PlanValue.AxisStart[0], "y": PlanValue.AxisStart[1], "z": 0.0},
            "fe0": {"x": 0.0, "y": 1.0, "z": 0.0},
            "ff8": 0,
            "fb0": 0.0,
            "fb8": PlanValue.AxisEnd[1] - PlanValue.AxisStart[1],
        },
    )
