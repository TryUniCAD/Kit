from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.CheckAxisViews import (
    CheckAxisViews,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadPrismAxes import (
    ReadPrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import (
    BuildPrismGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismScope import (
    CheckPrismScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import (
    ReadPrismBody,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# analytic geometry needs the original named stock and every axis display on one linked context
def ReadAxisGeom(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ModelValue: NativeModel,
    ColdValue: ColdOutput | None,
    BodyId: str,
    *,
    FrontStock: bool = False,
) -> PartGeometry:
    if ColdValue is None or LinkValue.ResolvedValue.ExtraFields is not None:
        raise ValueError("cache free origin axes require one actual named stock output")
    HeaderValue = ReadHeaderGraph(Archive.require("Header2"), 19000)
    ConfigValue = RequireNative(
        ManagerValue.RootValue.FieldsValue.get("f360"), "moPartConfiguration_c"
    )
    if (
        FieldInt(ConfigValue.FieldsValue, "f85c")
        != FieldInt(HeaderValue.FieldsValue, "f08") - 1
    ):
        raise ValueError(
            "cache free origin axis allocator disagrees with its configuration"
        )
    AxesValue = ReadPrismAxes(LinkValue, HeaderValue, IndexFeatures(LinkValue))
    Features = CheckPrismScope(
        LinkValue, ManagerValue, ModelValue, ColdValue, AxesValue=AxesValue
    )
    RelationValue = ModelValue.WidthDepth
    PlanValue = ReadPrismBody(
        LinkValue,
        Features,
        ColdValue,
        DormantValue=None if RelationValue is None else RelationValue.DormantValue,
    )
    if PlanValue.ReversedBlind == FrontStock:
        ProfileName = "forward Front" if FrontStock else "signed Top"
        raise ValueError(f"cache free origin axes require the {ProfileName} stock")
    Geometry = BuildPrismGeom(
        PlanValue, BodyId, ColdValue, CreatorValue=ColdValue.BossValue
    )
    BoundsValue = Geometry.TopologyValue.bounding_box
    if BoundsValue is None:
        raise ValueError("cache free origin axes lack their stock envelope")
    Views = CheckAxisViews(AxesValue, BoundsValue, SignedTop=PlanValue.ReversedBlind)
    CheckPrismPlane(Features, LinkValue.ConfigValue.RootValue, Views)
    return ReplaceValue(Geometry, AxesValue=AxesValue)
