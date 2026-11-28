from math import hypot as HypotValue
from struct import pack as PackValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialTail import (
    MakeRadialTail,
)
from convert.adapters.solidworks.Archive.Construction.Circles.RadialText import (
    RadialText,
)
from convert.adapters.solidworks.Archive.Construction.Circles.ReadRadialStyle import (
    ReadRadialStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the radial display derives its direction and distances from the actual path driver and authored label point
def MakePathView(
    ProfileValue: ArchiveNode,
    FrameValue: PlaneFrame,
    HandleValue: ArchiveNode,
    RadiusValue: float,
    InputValue: PartBuildInput,
) -> ArchiveNode:
    TextValue = (0.015, 0.004)
    DeltaX, DeltaY = TextValue[0], TextValue[1] - RadiusValue
    DistanceValue = HypotValue(DeltaX, DeltaY)
    CenterValue = MakePoint(YValue=RadiusValue)
    FieldsValue = MakeCommonView(
        HandleValue, InputValue.DesignIntent, InputValue.SelectedLeader, 20
    )
    StyleValue, IsSolid = ReadRadialStyle(
        ArchiveNode.RequireNode(ProfileValue.FieldsValue["owner"]), False
    )
    FieldsValue.update(StyleValue.ProjectionValue)
    FieldsValue.update(MakeRadialTail(False, IsSolid))
    FieldsValue.update(
        {
            "owner": ProfileValue,
            "f950": RadiusValue,
            "f7f8": "R",
            "f958": CenterValue,
            "f988": CenterValue,
            "fad0": RadiusValue,
            "f880": MakePoint(
                XValue=DeltaX / DistanceValue, YValue=DeltaY / DistanceValue
            ),
            "f8a8": DistanceValue / RadiusValue,
            "f8b0": DistanceValue - RadiusValue,
            "f3e0": FieldInt(FieldsValue, "f3e0") & ~0x200,
            "f8a4": (FieldInt(FieldsValue, "f8a4") & ~0x8050) | StyleValue.UnderText,
            "fb64": (FieldInt(FieldsValue, "fb64") & ~0x103000)
            | StyleValue.FlagValue
            | 0x800,
            "fb60": FieldInt(FieldsValue, "fb60") | 0x200,
        }
    )
    CastValue(dict[str, object], FieldRecord(FieldsValue["f6a0"]))["f38"] = RadialText(
        FrameValue, TextValue
    )
    CastValue(dict[str, object], FieldRecord(FieldsValue["f5b0"]))["data"] = PackValue(
        "<d", RadiusValue
    )
    return ArchiveNode(RuntimeClass("moDisplayRadialDim_c", 1), FieldsValue)
