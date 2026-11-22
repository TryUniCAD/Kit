from collections.abc import Sequence
from dataclasses import replace as ReplaceValue
from math import pi as PiValue
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.PartMass import PartMass
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckCircShell import (
    CheckCircShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckSavedRound import (
    CheckSavedRound,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleSolid import (
    CircleSolid,
)
from interchange import BrepPayload
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# verified native circle dimensions define the values only after the distinct physical shell agrees
def SavedCircleGeom(
    NativeValue: NativeModel,
    ModelValue: BrepModel,
    Payloads: Sequence[BrepPayload],
    BodyId: str,
) -> CircleSolid:
    AtomValue = NativeValue.SavedCircleAtom
    (SketchValue,) = NativeValue.sketches
    CircleValue = SketchValue.TypedCircle
    if AtomValue is None or CircleValue is None:
        raise ValueError("saved circle geometry lacks its live sketch and boss proof")
    CheckCircShell(ModelValue, Payloads, AtomValue)
    Result = CheckSavedRound(ModelValue, NativeValue)
    StartX, StartY = CircleValue.CenterValue
    Radius = CircleValue.RadiusValue
    Lower, Upper = (Value * 1000 for Value in Result["cap_offsets_m"])
    Centroid = (StartX, StartY, (Lower + Upper) / 2.0)
    Volume = Result["analytic_volume_m3"] * 1e9
    Bounds = BoundingBox(
        SpaceVector(StartX - Radius, StartY - Radius, Lower),
        SpaceVector(StartX + Radius, StartY + Radius, Upper),
    )
    Topology = TopologyCounts(
        solid_count=1,
        shell_count=len(ModelValue.shells),
        face_count=Result["face_count"],
        edge_count=Result["edge_count"],
        vertex_count=Result["closed_edge_representative_vertices"],
        bounding_box=Bounds,
        volume=Volume,
        surface_area=2 * PiValue * Radius * (Radius + abs(Upper - Lower)),
        valid=True,
    )
    (BodyValue,) = ModelValue.bodies
    Linked = ReplaceValue(
        ModelValue, bodies=(ReplaceValue(BodyValue, design_body_id=BodyId),)
    )
    return CircleSolid(Linked, Topology, PartMass(Volume, Centroid))
