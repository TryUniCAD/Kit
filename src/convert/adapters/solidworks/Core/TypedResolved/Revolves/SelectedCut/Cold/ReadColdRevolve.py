from math import pi as HalfTurn

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.CheckColdState import (
    CheckColdBodies,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdAtoms import (
    ReadColdAtoms,
)
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.CheckRevAngles import (
    CheckRevAngles,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.ReadRevGeom import (
    KRevolveGeomClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevBands import (
    CheckRevBands,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolveOwners import (
    ColdRevOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ReadColdRevPick import (
    ReadColdRevPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevBand import (
    ReadRevBand,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCutOps import (
    ReadRevCutOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCutTree import (
    ReadRevCutTree,
)


# cold revolve graphs need actual stock atoms and a selected reference but no realized result or saved chooser
def ReadColdRevolve(
    LinkValue: NativeLink, Manager: CmgrGraph, Model: NativeModel
) -> ColdRevOwners:
    CheckGeometry(LinkValue, Manager, Model)
    Features = ReadRevCutTree(LinkValue)
    First, Second, Cutter = ReadRevCutOps(LinkValue, Features)
    Operations = (First, Second, Cutter)
    if (
        LinkValue.ResolvedValue.ExtraFields is not None
        or ReadPrincAxis(First.FrameValue.SupportValue) not in ("x", "y")
        or Cutter.AngleValue.RadiansValue >= HalfTurn
        or Model.TypedGraph.get("status") != "supplemented"
        or len(Model.features) != len(Features)
        or {Value.object_id for Value in Model.features} != set(Features)
        or tuple(
            (Value.kind, Value.object_id, Value.profile_id)
            for Value in Model.operations
        )
        != tuple(
            (
                OperationKind,
                NativeNodeId(Value.NodeValue),
                NativeNodeId(Value.ProfileValue),
            )
            for OperationKind, Value in zip(
                ("revolve_join", "revolve_join", "revolve_cut"), Operations, strict=True
            )
        )
        or len(Model.sketches) != 3
        or {Value.object_id for Value in Model.sketches}
        != {NativeNodeId(Value.ProfileValue) for Value in Operations}
    ):
        raise ValueError("cold revolve requires its three supported linked operations")
    CheckRevBands(ReadRevBand(First), ReadRevBand(Second), ReadRevBand(Cutter))
    CheckPrismMgr(Manager)
    RootNode = LinkValue.ConfigValue.RootValue
    CheckPrismRoot(RootNode, 2)
    CheckPrismRels(RootNode)
    CheckPlanes(Model, Features)
    StockNodes = (First.NodeValue, Second.NodeValue)
    CheckColdBodies((*StockNodes, Cutter.NodeValue))
    Atoms, AtomIds = ReadColdAtoms(LinkValue, StockNodes)
    Selected, Wrapper = ReadColdRevPick(
        LinkValue, StockNodes, Cutter.NodeValue, AtomIds
    )
    Nodes = PrismNodes(
        LinkValue,
        Manager,
        AllowedClasses=KRevolveGeomClasses
        | {"moAtom_c", "moCompSolidBody_c", "moRevCut_c"},
    )
    CheckRevAngles(Nodes, First.EndValue, Second.EndValue, Cutter.EndValue)
    if tuple(
        GraphNode
        for GraphNode in Nodes
        if GraphNode.ClassValue.NameValue == "moCompSolidBody_c"
    ) != (Wrapper,):
        raise ValueError("cold revolve contains a detached stock selector")
    EndNodes = tuple(
        RequireNative(Value.NodeValue.FieldsValue.get("f8d8"), "moRevEndSpec_c")
        for Value in Operations
    )
    CheckTreeAlias(LinkValue, (RootNode, *Atoms, *EndNodes))
    return ColdRevOwners(LinkValue, (First, Second), Cutter, AtomIds, Selected, Wrapper)
