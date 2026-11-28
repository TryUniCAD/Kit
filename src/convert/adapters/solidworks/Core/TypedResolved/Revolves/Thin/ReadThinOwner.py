from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoots import (
    CheckPrismRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.ReadRevGeom import (
    KRevolveGeomClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.CheckThinDims import (
    CheckThinDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.MakeThinMerid import (
    MakeThinMerid,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinSpecs import (
    ReadThinSpecs,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinSweep import (
    ReadThinSweep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)

# thin cold readback requires every allocated owner of the single measured body profile
KThinGeomClasses = KRevolveGeomClasses - {"moRevolution_c"} | {
    "moRevolutionThin_c",
    "moThinSpec_c",
}


# complete frame and wire ownership must qualify before a portable thin definition can be attached
def ReadThinOwner(LinkValue: NativeLink, ManagerValue: CmgrGraph) -> ThinRevOwner:
    Features = IndexFeatures(LinkValue)
    NodesValue = PrismNodes(LinkValue, ManagerValue, AllowedClasses=KThinGeomClasses)
    CheckPrismRoots(
        Features,
        NodesValue,
        SolidClass="moRevolutionThin_c",
        RequiredClasses=(
            "moThinSpec_c",
            "moRevEndSpec_c",
            "moLineRef_w",
            "moCompSketchEntHandle_c",
        ),
    )
    RootValue = LinkValue.ConfigValue.RootValue
    CheckPrismRoot(RootValue)
    CheckPrismMgr(ManagerValue)
    CheckPrismRels(RootValue)
    (FeatureValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moRevolutionThin_c"
    )
    SweepValue = ReadThinSweep(LinkValue, FeatureValue, Features)
    ModeValue, FirstValue, SecondValue = ReadThinSpecs(FeatureValue)
    CheckThinDims(NodesValue, SweepValue.AngleValue, FirstValue, SecondValue)
    Meridian = MakeThinMerid(
        SweepValue.ProfileGraph,
        ModeValue,
        FirstValue.MetresValue,
        SecondValue.MetresValue,
    )
    WallsValue = (
        (FirstValue, SecondValue) if ModeValue == "two_sided" else (FirstValue,)
    )
    return ThinRevOwner(SweepValue, ModeValue, WallsValue, Meridian)
