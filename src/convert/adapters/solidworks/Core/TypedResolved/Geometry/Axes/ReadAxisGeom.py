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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.BindAxisStock import (
    BindAxisStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.CheckAxisScope import (
    CheckAxisScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.MakeBoxSolid import (
    MakeBoxSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadAxisStock import (
    ReadAxisStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
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
) -> tuple[NativeModel, PartGeometry]:
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
    Features = IndexFeatures(LinkValue)
    AxesValue = ReadPrismAxes(LinkValue, HeaderValue, Features)
    CheckAxisScope(LinkValue, ManagerValue, ModelValue, Features, ColdValue, AxesValue)
    StockValue = ReadAxisStock(LinkValue, Features, ColdValue.BossValue)
    Geometry = MakeBoxSolid(StockValue, ColdValue, AxesValue, BodyId)
    BoundsValue = Geometry.TopologyValue.bounding_box
    if BoundsValue is None:
        raise ValueError("cache free origin axes lack their stock envelope")
    Views = CheckAxisViews(AxesValue, BoundsValue)
    CheckPrismPlane(Features, LinkValue.ConfigValue.RootValue, Views)
    return BindAxisStock(ModelValue, StockValue, Features), Geometry
