from struct import pack as PackValues

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialTail import (
    MakeRadialTail,
)
from convert.adapters.solidworks.Archive.Construction.Circles.RadialText import (
    RadialText,
)
from convert.adapters.solidworks.Archive.Construction.Circles.ReadRadialPlace import (
    ReadRadialPlace,
)
from convert.adapters.solidworks.Archive.Construction.Circles.ReadRadialStyle import (
    ReadRadialStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the circle display uses a common native view and computed radial text and leader geometry
def MakeRadialView(
    GraphValue: ProfileGraph,
    HandleValue: ArchiveNode,
    LengthValue: float,
    TextPoint: tuple[float, float],
    IsDiameter: bool,
    DesignIntent: bool,
    SelectedLeader: int,
    *,
    NormalOffset: float = 0.0,
) -> ArchiveNode:
    TextKind = 17 if IsDiameter else 20
    FieldsValue = MakeCommonView(HandleValue, DesignIntent, SelectedLeader, TextKind)
    ModelValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    StyleValue, IsSolid = ReadRadialStyle(ModelValue, IsDiameter)
    FieldsValue.update(StyleValue.ProjectionValue)
    FieldsValue.update(MakeRadialTail(IsDiameter, IsSolid))
    FieldsValue.update(ReadRadialPlace(GraphValue, TextPoint, LengthValue, IsDiameter))
    FieldsValue.update(
        {
            "owner": GraphValue.ProfileValue,
            "f950": LengthValue,
            "f7f8": "<MOD-DIAM>" if IsDiameter else "R",
            "f3e0": FieldInt(FieldsValue, "f3e0") & ~0x200,
            "f8a4": (FieldInt(FieldsValue, "f8a4") & ~0x8050) | StyleValue.UnderText,
            "fb64": (FieldInt(FieldsValue, "fb64") & ~0x103000)
            | StyleValue.FlagValue
            | 0x800,
            "fb60": FieldInt(FieldsValue, "fb60") | 0x200,
        }
    )
    TextValue = dict(RequireRecord(FieldsValue["f6a0"]))
    TextValue["f38"] = RadialText(GraphValue.FrameValue, TextPoint, NormalOffset)
    FieldsValue["f6a0"] = TextValue
    CacheValue = dict(RequireRecord(FieldsValue["f5b0"]))
    CacheValue["data"] = PackValues("<d", LengthValue)
    FieldsValue["f5b0"] = CacheValue
    return ArchiveNode(RuntimeClass("moDisplayRadialDim_c", 1), FieldsValue)
