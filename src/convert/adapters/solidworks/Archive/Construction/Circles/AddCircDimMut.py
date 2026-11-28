from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialRef import (
    MakeRadialRef,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialVal import (
    MakeRadialVal,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialView import (
    MakeRadialView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import (
    MakeOriginFix,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireDimRows import (
    RequireDimRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# a fixed centre and its radial value must publish only after all owned references and display fields are ready
def AddCircDimMut(
    GraphValue: ProfileGraph,
    TextPoint: tuple[float, float],
    IsDiameter: bool,
    DesignIntent: bool,
    SelectedLeader: int,
    Allocator: PersistentIds,
) -> DimensionGraph:
    Geometry = NeedCircle(GraphValue)
    if GraphValue.FrameValue.OriginValue != (0.0, 0.0, 0.0):
        raise ValueError("radial dimension requires a principal support at origin")
    FieldsValue = RequireDimRows(Geometry.SketchValue)
    ValueNode = MakeRadialVal(GraphValue, IsDiameter)
    Handle = MakeRadialRef(GraphValue, ValueNode)
    Parameter = ArchiveNode.RequireNode(ValueNode.FieldsValue["f28"])
    LengthValue = RequireScalar(Parameter.FieldsValue["f58"])
    Display = MakeRadialView(
        GraphValue,
        Handle,
        LengthValue,
        TextPoint,
        IsDiameter,
        DesignIntent,
        SelectedLeader,
    )
    Constraint = MakeOriginFix(Geometry.SketchValue, Geometry.CenterValue)
    DisplayList = ArchiveNode.RequireNode(FieldsValue["f118"])
    _ = Allocator.AllocateMut(ValueNode, "f50")
    Relations = ({"d": Constraint.FieldsValue},)
    Values = ({"d": ValueNode},)
    Items = ({"o": Display},)
    FieldsValue.update({"log_g1": Relations, "nlog1": len(Relations)})
    FieldsValue.update({"val_g1": Values, "ng1": len(Values)})
    DisplayList.FieldsValue.update({"items": Items, "n": len(Items)})
    Geometry.CenterValue.FieldsValue["f20"] = len(Relations)
    Geometry.ArcValue.FieldsValue["f20"] = len(Values)
    return DimensionGraph(Parameter, ValueNode, Handle, Display)
