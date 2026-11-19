from dataclasses import dataclass

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Extrude.Polygon.PrismRing import MeasureRing
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import BlindPlan
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import PolygonGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from para.DownstreamIds import install_part_downstream
from para.Partition import frame_payloads, write_payloads
from para.Tracking import signed_dword
from para.rectangle.Allocate import Ref, allocate_marks, allocate_updates, positive_i32, prism_tracking, require
from para.rectangle.AttributeChains import register_attributes
from para.rectangle.Geometry import FaceRole, topology_nodes
from para.rectangle.RectangleAttributes import prism_installs
from para.rectangle.RectanglePartition import complete_topology, finish_prism_projection


@dataclass(frozen=True)
class SdkPrism:
    projection: object
    marks: object
    updates: object
    tracking: object
    body: object
    face_roles: dict
    volume_mm3: float
    area_mm2: float
    bounds_mm: object
    atom_id: int

    def stream(self):
        return frame_payloads(write_payloads(self.projection.partition))


def pairs(points):
    return zip(points, points[1:] + points[:1], strict=True)


def edge_key(first, second):
    return frozenset(((first.x, first.y), (second.x, second.y)))


def design_geometry(candidate):
    plan, profile = candidate.PlanValue, candidate.ProfileValue
    require(isinstance(plan, BlindPlan) and isinstance(profile.GeometryValue, PolygonGraph),
            "a prism partition requires an actual planar line loop")
    frame = profile.FrameValue
    require(
        (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue)
        == ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "the initial prism partition profile uses the canonical Front plane",
    )
    points = tuple(PlaneVector(x * 1000, y * 1000) for x, y in plan.VerticesValue)
    lines = tuple(LineGeometry(first, second) for first, second in pairs(points))
    ordered, _, _ = MeasureRing(points)
    source_ids = {
        edge_key(first, second): FieldInt(node.FieldsValue, "f08")
        for (first, second), node in zip(pairs(points), profile.GeometryValue.LineValues, strict=True)
    }
    require(len(source_ids) == len(set(source_ids.values())) == len(points),
            "each actual profile segment must supply a distinct identity")
    placement = Transform(*(SpaceVector(*axis) for axis in (
        frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue,
    )))
    body, volume, area, bounds = BuildPrism(plan.BodyId, placement, lines, 0.0, plan.DepthValue * 1000)
    start, end, *sides = body.faces
    roles = {start.id: FaceRole(True, 0), end.id: FaceRole(True, 1)}
    roles.update(
        (side.id, FaceRole(False, source_ids[edge_key(first, second)]))
        for side, (first, second) in zip(sides, pairs(ordered), strict=True)
    )
    return body, roles, volume, area, bounds


def sdk_prism(candidate, session, appearance, previous_faces=0, *, downstream=None):
    require(type(candidate) is PartCandidate and candidate.CutValue is None,
            "the prism partition requires an actual fresh boss part")
    manager = candidate.SystemValue.RootValue.FieldsValue["fd88"]
    require(not manager["atoms"] and manager["n6c"] == 0 and manager["fa8"] == 0,
            "the prism allocation requires its unused actual body manager")
    part_body, roles, volume, area, bounds = design_geometry(candidate)
    marks = allocate_marks(session)
    updates = allocate_updates(session, candidate.HeaderValue.FieldsValue)
    boss = candidate.BossValue.FeatureValue
    feature_id = positive_i32(FieldInt(boss.FieldsValue, "f08"), "actual prism feature")
    atom_id = positive_i32(FieldInt(manager, "f260") + 1, "next body atom")
    creation = signed_dword(DatumTime(candidate.HeaderValue, feature_id))
    tracking = prism_tracking(part_body, session, updates, feature_id, atom_id, ReadNodeName(boss))
    topology, next_id = complete_topology(topology_nodes(part_body, marks))
    installs = tuple(prism_installs(part_body, roles, tracking, feature_id, creation, appearance, previous_faces))
    if downstream is not None:
        installs = install_part_downstream(topology, installs, downstream)
    active, nontransmitted, next_id = register_attributes(topology, Ref(part_body.bodies[0].id), installs, next_id)
    projection = finish_prism_projection(active, next_id, marks, nontransmitted)
    return SdkPrism(projection, marks, updates, tracking, part_body, roles, volume, area, bounds, atom_id)
