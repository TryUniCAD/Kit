from collections import Counter
from itertools import product as Cartesian
from math import isclose as IsClose

from convert.adapters.freecad.BodyLineage.BoxShapeOwner import (
    FindShapeData,
    ReadShapeNodes,
)
from convert.adapters.freecad.Native import NativeArchive, NativeObject
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismTrims import (
    CheckPrismTrims,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    ReadCarriers,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxGeometry import (
    CheckBoxCache,
)
from convert.Geometry.Opencascade import DecodeAsciiBrep
from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorSpace import SpaceVector


# a retained source cache must be one closed solid with a unique shell and literal face ownership
def CheckStockSolid(ModelValue: BrepModel, FeatureId: str) -> None:
    (BodyValue,) = ModelValue.bodies
    (RegionValue,) = ModelValue.regions
    (ShellUse,) = ModelValue.shell_uses
    (ShellValue,) = ModelValue.shells
    if (
        BodyValue.transform != KTransformIdentity
        or BodyValue.design_body_id != FeatureId
        or BodyValue.region_ids != (RegionValue.id,)
        or BodyValue.wire_ids
        or BodyValue.vertex_ids
        or not RegionValue.solid
        or RegionValue.shell_use_ids != (ShellUse.id,)
        or ShellUse.shell_id != ShellValue.id
        or ShellUse.reversed
        or not ShellValue.closed
        or ModelValue.wires
        or len(ModelValue.face_uses) != 6
        or len(ShellValue.face_use_ids) != 6
        or set(ShellValue.face_use_ids)
        != {UseValue.id for UseValue in ModelValue.face_uses}
        or {UseValue.face_id for UseValue in ModelValue.face_uses}
        != {FaceValue.id for FaceValue in ModelValue.faces}
        or ModelValue.validate(frozenset({FeatureId}))
    ):
        raise ValueError("FreeCAD stock shape is not its actual closed planar solid")


# the six positively sized walls must match their actual ordered corner incidence and line carriers
def CheckStockRings(
    ModelValue: BrepModel,
    Minimum: tuple[float, float, float],
    Maximum: tuple[float, float, float],
) -> None:
    Topology = BrepTopology(ModelValue)
    Carriers = ReadCarriers(ModelValue)
    CheckPrismTrims(Topology, Carriers)
    Centre = SpaceVector(
        *((First + Other) / 2 for First, Other in zip(Minimum, Maximum, strict=True))
    )
    FaceUses = {UseValue.face_id: UseValue for UseValue in ModelValue.face_uses}
    Points = Topology.vertex_by_id
    Corners = {
        KeyValue: (Vertex.point.x, Vertex.point.y, Vertex.point.z)
        for KeyValue, Vertex in Points.items()
    }
    Rings: set[frozenset[tuple[float, float, float]]] = set()
    for PlaneValue in Carriers.PlanesValue:
        FaceValue = Carriers.PlaneOwners[PlaneValue.id]
        Outward = FaceValue.same_sense != FaceUses[FaceValue.id].reversed
        NormalSense = DotVector(
            OffsetVector(PlaneValue.origin, Centre, -1.0), PlaneValue.normal
        )
        (LoopId,) = FaceValue.loop_ids
        LoopValue = Topology.loops[LoopId]
        Edges = tuple(
            Topology.edges[Topology.coedges[UseId].edge_id]
            for UseId in LoopValue.coedge_ids
        )
        EndIds = {
            VertexId
            for EdgeValue in Edges
            for VertexId in (EdgeValue.start_vertex_id, EdgeValue.end_vertex_id)
        }
        if (
            not LoopValue.outer
            or len(Edges) != 4
            or len(EndIds) != 4
            or NormalSense == 0.0
            or (NormalSense > 0.0) != Outward
            or any(EdgeValue.degenerate for EdgeValue in Edges)
            or any(
                abs(
                    DotVector(
                        OffsetVector(Points[VertexId].point, PlaneValue.origin, -1.0),
                        PlaneValue.normal,
                    )
                )
                > 1e-10
                for VertexId in EndIds
            )
        ):
            raise ValueError("FreeCAD stock shape has a nonrectangular planar trim")
        Rings.add(frozenset(Corners[VertexId] for VertexId in EndIds))
    Expected = {
        frozenset(
            Corner
            for Corner in Cartesian(*zip(Minimum, Maximum, strict=True))
            if Corner[AxisIndex] == Level
        )
        for AxisIndex in range(3)
        for Level in (Minimum[AxisIndex], Maximum[AxisIndex])
    }
    UseCounts = Counter(Value.edge_id for Value in ModelValue.coedges)
    UniqueUses = {
        UseId for LoopValue in ModelValue.loops for UseId in LoopValue.coedge_ids
    }
    if (
        Rings != Expected
        or UseCounts != Counter({Value.id: 2 for Value in ModelValue.edges})
        or UniqueUses != Topology.coedges.keys()
        or len(ModelValue.loops) != 6
        or any(
            sum(
                not IsClose(First, Second, rel_tol=0, abs_tol=1e-10)
                for First, Second in zip(
                    Corners[EdgeValue.start_vertex_id],
                    Corners[EdgeValue.end_vertex_id],
                    strict=True,
                )
            )
            != 1
            for EdgeValue in ModelValue.edges
        )
    ):
        raise ValueError(
            "FreeCAD stock shape does not match its literal box dimensions"
        )


# source geometry comes from the selected primitive shape rather than the active document body
def ReadStockShape(
    Document: CadDocument,
    ArchiveValue: NativeArchive,
    OwnerValue: NativeObject,
    FeatureId: str,
    Sizes: tuple[float, float, float],
    *,
    Minimum: tuple[float, float, float] = (0.0, 0.0, 0.0),
    Placed: bool = False,
) -> BrepModel:
    Property, Nodes = ReadShapeNodes(OwnerValue)
    TagsValue = tuple(Value.tag for Value in Nodes)
    if TagsValue != ("Part",) and (
        not Placed
        or TagsValue != ("Part", "ElementMap")
        or Nodes[1].attrib
        or len(Nodes[1])
    ):
        raise ValueError("FreeCAD stock shape has unsupported extra element owners")
    Payload = FindShapeData(
        Document, ArchiveValue, OwnerValue, Property, Nodes[0], "feature_id", FeatureId
    )
    if Payload.data is None or Payload.attributes.get("freecad_sidecars"):
        raise ValueError(
            "FreeCAD stock requires its actual unindexed source shape data"
        )
    ModelValue = DecodeAsciiBrep(Payload.data, IdPrefix="stock", DesignBodyId=FeatureId)
    if ModelValue is None:
        raise ValueError("FreeCAD stock shape is not a supported OCCT analytical solid")
    Maximum = (Minimum[0] + Sizes[0], Minimum[1] + Sizes[1], Minimum[2] + Sizes[2])
    CheckBoxCache(ModelValue, Minimum, Maximum)
    CheckStockSolid(ModelValue, FeatureId)
    CheckStockRings(ModelValue, Minimum, Maximum)
    return ModelValue
