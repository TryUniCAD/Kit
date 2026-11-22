from struct import pack as PackValues

from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadRectPlace import (
    ReadRectPlace,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# complete point distance displays share native common construction while retaining their own actual style geometry annotation and routing inputs
def MakeRectDisplay(
    GraphValue: ProfileGraph,
    HandleValue: ArchiveNode,
    LengthValue: float,
    IndexValue: int,
    PointIndices: tuple[int, int],
    AnnotationId: int,
    InputValue: RectDimInput,
    StyleValue: LinearStyle,
) -> ArchiveNode:
    TextPoint = (InputValue.WidthText, InputValue.HeightText)[IndexValue]
    FieldsValue = MakeCommonView(
        HandleValue, InputValue.DesignIntent, InputValue.SelectedLeader, 18
    )
    FieldsValue.update(MakeDistTail())
    FieldsValue.update(StyleValue.ProjectionValue)
    FieldsValue.update(
        ReadRectPlace(
            tuple(
                ReadPointPair(Value) for Value in GraphValue.GeometryValue.PointValues
            ),
            IndexValue,
            PointIndices,
            LengthValue,
            TextPoint,
        )
    )
    FieldsValue["owner"] = GraphValue.ProfileValue
    FieldsValue["f58"] = AnnotationId
    FieldsValue["f8a4"] = (
        (FieldInt(FieldsValue, "f8a4") & ~0x50) | StyleValue.UnderText | 0x2000000
    )
    FieldsValue["fb64"] = (
        FieldInt(FieldsValue, "fb64") & ~0x103000
    ) | StyleValue.FlagValue
    Routing = InputValue.RouteCenter
    RouteCenter = Routing if isinstance(Routing, bool) else Routing[IndexValue]
    FieldsValue["f1014"] = 0x800 if RouteCenter else 0
    TextValue = dict(RequireRecord(FieldsValue["f6a0"]))
    TextValue["f38"] = MakePoint(
        XValue=TextPoint[0],
        YValue=TextPoint[1],
        ZValue=InputValue.TextDepths[IndexValue],
    )
    FieldsValue["f6a0"] = TextValue
    CacheValue = dict(RequireRecord(FieldsValue["f5b0"]))
    CacheValue["data"] = PackValues("<d", LengthValue)
    FieldsValue["f5b0"] = CacheValue
    return ArchiveNode(RuntimeClass("moDisplayDistanceDim_c", 1), FieldsValue)
