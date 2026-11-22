from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLocalRef import (
    MakeLocalRef,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.MakePathParam import (
    MakePathParam,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.MakePathView import (
    MakePathView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the radial sketch value and its display share the same local handle and persistent identity
def MakePathDimMut(
    ProfileValue: ArchiveNode,
    FrameValue: PlaneFrame,
    SketchValue: ArchiveNode,
    ArcValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
) -> DimensionGraph:
    ParameterValue, DriverValue = MakePathParam(
        ProfileValue, SketchValue, ArcValue, PointValues
    )
    HandleValue = ArchiveNode(
        RuntimeClass("moSkDimHandleRadial_c", 1),
        {
            **MakeLocalRef(FieldInt(ProfileValue.FieldsValue, "f2b0")),
            "owner": ProfileValue,
            "_values": (DriverValue,),
            "has_f120": 0,
            "has_f128": 0,
            "f130": None,
            "f138": None,
            "f140": None,
            "f148": None,
            "f150": 0,
            "fe8": None,
            "f100": None,
            "f154": -1,
            "f118": 0,
            "ff0": SketchValue,
            "ff8": 0,
        },
    )
    RadiusValue = RequireScalar(ParameterValue.FieldsValue["f58"])
    DisplayValue = MakePathView(
        ProfileValue, FrameValue, HandleValue, RadiusValue, InputValue
    )
    _ = Allocator.AllocateMut(DriverValue, "f50")
    return DimensionGraph(ParameterValue, DriverValue, HandleValue, DisplayValue)
