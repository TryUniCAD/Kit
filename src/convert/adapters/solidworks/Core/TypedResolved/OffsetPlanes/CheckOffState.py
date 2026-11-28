from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckGeometryState import (
    CheckGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleClasses import (
    KCircleClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# analytic reconstruction requires a complete linked inventory so detached owners cannot change geometry
def CheckOffState(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    Features: Mapping[int, ArchiveNode],
    OffsetId: int,
) -> None:
    CheckGeometry(LinkValue, ManagerValue, ModelValue)
    if (
        ModelValue.TypedGraph.get("status") != "supplemented"
        or len(ModelValue.sketches) != 1
        or len(ModelValue.operations) != 1
        or len(ModelValue.features) != len(Features)
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
    ):
        raise ValueError("offset plane part has unresolved feature owners")
    NodesValue = PrismNodes(
        LinkValue, ManagerValue, AllowedClasses=KCircleClasses | {"moFaceRefPlnData_c"}
    )
    CheckPrismRoots(
        Features,
        NodesValue,
        RequiredClasses=(
            "moEndSpec_c",
            "moFromEndSpec_c",
            "moDisplayRadialDim_c",
            "moSkDimHandleRadial_c",
            "sgCircleDim",
            "moFaceRefPlnData_c",
        ),
        HasOffset=True,
    )
    RootValue = LinkValue.ConfigValue.RootValue
    if any(
        RootValue.FieldsValue[NameValue] is not None
        for NameValue in ("fa48", "fa50", "f9d8")
    ):
        raise ValueError("offset plane part requires its absent optional model lists")
    CheckPrismRoot(RootValue, NullRect=True)
    CheckPrismRels(RootValue)
    CheckPrismMgr(ManagerValue)
    Ordinary = {
        Identity: NodeValue
        for Identity, NodeValue in Features.items()
        if Identity != OffsetId
    }
    CheckPrismPlane(Ordinary, RootValue, FrontOnly=False)
    CheckPlanes(
        ReplaceValue(
            ModelValue,
            planes=tuple(
                Plane for Plane in ModelValue.planes if Plane.object_id != OffsetId
            ),
        ),
        Ordinary,
    )
