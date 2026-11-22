from collections.abc import Sequence
from dataclasses import replace as ReplaceValue
from math import pi as PiValue

from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.CircularPartition import (
    CheckRoundBody,
    ReadShellAtom,
)
from convert.adapters.solidworks.Core.Partition.PartMass import PartMass
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleSolid import (
    CircleSolid,
)
from interchange import BrepPayload
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# the saved world shell must carry the same active body atom as the actual boss
def CheckCircShell(
    ModelValue: BrepModel, Payloads: Sequence[BrepPayload], AtomValue: int
) -> None:
    Sources = tuple(
        Payload
        for Payload in Payloads
        if Payload.source_stream == KPartitionStream and Payload.kind == "partition"
    )
    if len(Sources) != 1 or Sources[0].data is None:
        raise ValueError("saved circle lacks its unique active partition payload")
    if (
        len(ModelValue.bodies) != 1
        or ModelValue.bodies[0].design_body_id
        or ReadShellAtom(Sources[0].data, ModelValue)["body_atom_id"] != AtomValue
    ):
        raise ValueError(
            "saved circle partition shell disagrees with the live body atom"
        )


# verified native circle dimensions define the values only after the distinct physical shell agrees
def SavedCircleGeom(
    NativeValue: NativeModel,
    ModelValue: BrepModel,
    Payloads: Sequence[BrepPayload],
    BodyId: str,
) -> CircleSolid:
    AtomValue = NativeValue.SavedCircleAtom
    (SketchValue,) = NativeValue.sketches
    (Operation,) = NativeValue.operations
    CircleValue = SketchValue.TypedCircle
    FrameValue = SketchValue.TypedFrame
    Length = Operation.length_mm
    if (
        AtomValue is None
        or CircleValue is None
        or FrameValue is None
        or Length is None
        or FrameValue.z_axis != SpaceVector(0.0, 0.0, 1.0)
        or Operation.direction_code != 0
    ):
        raise ValueError("saved circle geometry lacks its live sketch and boss proof")
    CheckCircShell(ModelValue, Payloads, AtomValue)
    AxisValue = (FrameValue.z_axis.x, FrameValue.z_axis.y, FrameValue.z_axis.z)
    StartX, StartY = CircleValue.CenterValue
    Radius = CircleValue.RadiusValue
    Origin = (StartX / 1000, StartY / 1000, 0.0)
    Result = CheckRoundBody(ModelValue, Origin, AxisValue, Length / 1000, Radius / 1000)
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
