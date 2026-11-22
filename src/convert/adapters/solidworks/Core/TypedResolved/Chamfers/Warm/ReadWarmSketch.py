from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckOriginGeom import (
    CheckOriginGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedChain import (
    CheckSavedChain,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform


# saved relation state remains supported only for the actual rectangular principal profile
def ReadWarmSketch(
    LinkValue: NativeLink,
    Profile: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    DepthValue: float,
) -> tuple[PrismPlan, LineLoop]:
    RootValue = LinkValue.ConfigValue.RootValue
    DatumKinds = tuple(
        ReadDatumFrame(Value)[1]
        for Value in Features.values()
        if Value.ClassValue.NameValue == "moRefPlane_c"
    )
    (OriginValue,) = (
        Value
        for Value in Features.values()
        if Value.ClassValue.NameValue == "moOriginProfileFeature_c"
    )
    FrameValue = ReadPrismFrame(Profile, RootValue, Features)
    if (
        set(DatumKinds) != {1, 2, 3}
        or len(DatumKinds) != 3
        or FrameValue != Transform()
    ):
        raise ValueError("saved chamfer stock has alternate datum ownership")
    CheckOriginGeom(OriginValue)
    CheckPrismProf(Profile, IsSaved=True)
    Sketch = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    Fields = Sketch.FieldsValue
    if (
        any(
            Fields.get(FieldName) != 0 for FieldName in ("f188", "f18c", "f190", "f134")
        )
        or Fields.get("f578") != 1
        or NativeRecord(Fields.get("f570")) != dict.fromkeys("xyz", 0.0)
    ):
        raise ValueError("saved chamfer stock has alternate sketch evaluation state")
    DimsValue = ReadLineDims(Sketch, LinkValue)
    LoopValue = ReadLineLoop(Sketch, LinkValue, DimsValue)
    Points = {Value.PositionValue for Value in LoopValue.PointsValue.values()}
    if (
        DimsValue.DriverValues
        or DimsValue.OriginValue is not None
        or len(DimsValue.AxisValues) != 4
        or len(LoopValue.PointsValue) != 4
        or len(LoopValue.LinesValue) != 4
        or len({XValue for XValue, _ in Points}) != 2
        or len({YValue for _, YValue in Points}) != 2
        or len(LoopValue.RegionValues) != 1
    ):
        raise ValueError(
            "saved chamfer stock has alternate or incomplete rectangle constraints"
        )
    CheckDimGraph(LoopValue, DimsValue)
    CheckSavedChain(LinkValue, Profile.FieldsValue.get("d5c0"), LoopValue)
    return PrismPlan(FrameValue, MakePrismLines(LoopValue), DepthValue, {}), LoopValue
