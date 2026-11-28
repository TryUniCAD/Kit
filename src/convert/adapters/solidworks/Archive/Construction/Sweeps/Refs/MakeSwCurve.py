from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Refs.CheckSwOwner import (
    CheckSwOwner,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the section reuses its last access clock and actual active configuration while the path stays live and unresolved
def SwCurveFields(
    HeaderValue: ArchiveNode,
    ProfileValue: ArchiveNode,
    ConfigValue: ArchiveNode,
    IsSection: bool,
) -> dict[str, object]:
    return {
        "f68": int(IsSection),
        "f60": None,
        "f6c": 0,
        "f08": FieldInt(HeaderValue.FieldsValue, "f40") if IsSection else 101,
        "has_f10": 0,
        "has_f18": 0,
        "f0c": FieldInt(ConfigValue.FieldsValue, "f08") if IsSection else -1,
        "f20": 0,
        "f74": -12345,
        "f78": -12345,
        "f7c": -12345,
        "f50": 0,
        "f70": FieldInt(ProfileValue.FieldsValue, "f2b0"),
        "f34": 0,
        "f30": 0,
        "f98": 0,
        "f38": -1,
        "fb0": 0.0,
        "fb8": 1.0,
        "has_fc8": int(IsSection),
        "fd0": 0xFFFFFFFF,
        "fd4": -1,
        "fe0": None,
        "fd8": None,
        "fe8": None,
    }


# the two typed curve picks derive native component identity and creation time from the actual parent owners
def MakeSwCurve(
    SystemValue: PartSystem,
    HeaderValue: ArchiveNode,
    ProfileValue: ArchiveNode,
    AxisValue: Literal["x", "z"],
    GhostId: int,
    DriverValue: DimensionGraph,
) -> ArchiveNode:
    CheckSwOwner(SystemValue, ProfileValue, AxisValue, DriverValue)
    if type(GhostId) is not int or GhostId <= 0:
        raise ValueError("sweep curve pick requires its actual ghost identity")
    (ConfigValue,) = SystemValue.ConfigValues
    ProfileId = NativeNodeId(ProfileValue)
    ComponentFields = CompRefFields(
        ArchiveNode.RequireNode(SystemValue.RootValue.FieldsValue["f990"])
    )
    ComponentFields.update(
        ff0={"f00": ProfileId, "f08": DatumTime(HeaderValue, ProfileId)}, f20=GhostId
    )
    IsSection = AxisValue == "x"
    FieldsValue = SwCurveFields(HeaderValue, ProfileValue, ConfigValue, IsSection)
    FieldsValue["f58"] = ArchiveNode(
        RuntimeClass("moCompProfile_c", 1), ComponentFields
    )
    if IsSection:
        DiameterValue = RequireScalar(DriverValue.ParameterValue.FieldsValue["f58"])
        FieldsValue["fc8"] = {
            "CircleValue": CircleGeometry(PlaneVector(0.0, 0.0), DiameterValue / 2)
        }
    return ArchiveNode(RuntimeClass("moGeneralCurveRef_w", 1), FieldsValue)
