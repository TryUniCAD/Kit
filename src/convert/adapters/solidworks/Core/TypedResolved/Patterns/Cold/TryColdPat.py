from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.BindPatModel import (
    BindPatModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.BuildColdPat import (
    BuildColdPat,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.HasColdPat import (
    HasColdPat,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.CheckPatViews import (
    CheckPatViews,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatError import (
    ColdPatError,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatPart import (
    ColdPatPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatLook import (
    ReadPatLook,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ReadPatStocks import (
    ReadPatStocks,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import (
    ReadPatOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody


# cache free histories need linked format owners and consistent neutral stock bindings
def TryColdPat(
    Archive: SldprtArchive, ModelValue: NativeModel, Settings: ReadOptions, BodyId: str
) -> tuple[NativeModel, ColdPatPart] | None:
    if not HasColdPat(Archive, ModelValue, Settings):
        return None
    try:
        if ModelValue.active_configuration_id != 0:
            raise ValueError("cold linear pattern requires physical configuration zero")
        LinkValue = ReadNativeLink(Archive, 0, PartPattern=True)
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
        CheckGeometry(LinkValue, Manager, ModelValue)
        CheckPrismMgr(Manager)
        RootValue = LinkValue.ConfigValue.RootValue
        CheckPrismRoot(RootValue, 3, HasAnnotations=True)
        CheckPrismRels(RootValue)
        CheckPatViews(LinkValue)
        OwnerValue = ReadPatOwner(LinkValue, Header)
        LookValue = ReadPatLook(LinkValue, OwnerValue)
        if LinkValue.ResolvedValue.ExtraFields is not None:
            raise ValueError("cache free pattern has a resolved body map")
        PlateValue, SeedValue = ReadPatStocks(LinkValue, OwnerValue)
        Geometry = BuildColdPat(
            LinkValue, OwnerValue, (PlateValue.PlanValue, SeedValue.PlanValue), BodyId
        )
        NativeId = NativeNodeId(OwnerValue.NodeValue)
        ProofValue = NativeNodeSpan(LinkValue, OwnerValue.NodeValue)
        BodyValue = DesignBody(
            id=BodyId,
            name=ReadNativeName(OwnerValue.NodeValue),
            final_feature_id=f"sldprt:feature:{NativeId}",
            topology=Geometry.TopologyValue,
            attributes=FreezeMapping(
                {
                    "native_object_id": NativeId,
                    "solidworks.body_centroid_mm": Geometry.EvidenceValue[
                        "centroid_mm"
                    ],
                    "solidworks.native_kernel_identity": False,
                }
            ),
            provenance=TypedProvenance(ProofValue, str(NativeId)),
        )
        PatternValue = ColdPatPart(
            LinkValue,
            OwnerValue,
            Geometry,
            (BodyValue,),
            (PlateValue, SeedValue),
            LookValue,
        )
        return BindPatModel(ModelValue, PatternValue), PatternValue
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        if Settings.strict:
            raise ColdPatError() from ErrorInfo
        return None
