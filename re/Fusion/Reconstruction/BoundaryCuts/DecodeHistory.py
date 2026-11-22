import argparse
import hashlib
import json
import math
from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import ReadVertexPoint
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckEdgeUses import CheckEdgeUses
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckLineEdge import CheckLineEdge
from convert.Formats.Fusion.BrepCodec.Journal.Planar.VectorMath import CrossProduct, DotProduct, Normalize, Subtract
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes


def measure(history, state_id):
    table = MakeLiveTable(history, state_id)
    bodies = [ref for ref in table.LiveSlots if isinstance(table.Entities[ref], BodyNode)]
    if len(bodies) != 1:
        raise ValueError("Research measurement requires one body")
    if table.Entities[bodies[0]].TransformRef != -1:
        raise ValueError("Research measurement does not handle body placement")
    faces = ReadBodyFaces(table, bodies[0])
    CheckEdgeUses(table, faces)
    vertices = sorted({use.StartVertex for face in faces for use in face.BoundaryUses})
    points = {ref: ReadVertexPoint(table, ref) for ref in vertices}
    edges = {use.EdgeRef for face in faces for use in face.BoundaryUses}
    if len(vertices) - len(edges) + len(faces) != 2:
        raise ValueError("Research body violates genus zero Euler characteristic")
    for ref in edges:
        CheckLineEdge(table, ref)
    volume, area = 0.0, 0.0
    rings = []
    for face in faces:
        ring = [points[use.StartVertex] for use in face.BoundaryUses]
        normal = Normalize(face.Surface.Normal)
        if face.Reversed:
            normal = tuple(-amount for amount in normal)
        if any(abs(DotProduct(Subtract(point, face.Surface.OriginCm), normal)) > 1e-7 for point in ring):
            raise ValueError("Research face is not on its declared native plane")
        vector = tuple(sum(CrossProduct(ring[index], ring[(index + 1) % len(ring)])[axis] for index in range(len(ring))) / 2 for axis in range(3))
        signed_area = DotProduct(vector, normal)
        if signed_area <= 1e-12:
            raise ValueError("Research face has nonpositive outward area")
        area += signed_area
        volume += sum(DotProduct(ring[0], CrossProduct(ring[index], ring[index + 1])) / 6 for index in range(1, len(ring) - 1))
        rings.append(ring)
    return {"state_id": table.StateId, "volume_cm3": volume, "area_cm2": area, "faces": len(faces), "edges": len(edges), "vertices": len(vertices), "min_cm": [min(point[axis] for point in points.values()) for axis in range(3)], "max_cm": [max(point[axis] for point in points.values()) for axis in range(3)], "rings_cm": rings}


def feature_trace(graph, feature):
    entry = {"id": feature.Identity, "class": feature.ClassName, "name": feature.Fields["featureUserName"]}
    if feature.ClassName != "DcExtrudeFeature":
        return entry
    entry.update({key: feature.Fields[key] for key in ("booleanOperation", "directionType", "startModelHS", "endModelHS")})
    entry["parameters"] = []
    for key in ("rAlongDistance", "rTaperAngle"):
        binding = graph.Resolve(feature.Fields[key])
        parameter = graph.Resolve(binding.Fields["parameter"])
        entry["parameters"].append({"binding_id": binding.Identity, "parameter_id": parameter.Identity, "role": parameter.Fields["name"], "value": parameter.Fields["value"]})
    entry["targets"] = []
    for reference in LinkedNodes(graph, feature, "targetDataRefs"):
        for operand in LinkedNodes(graph, reference, "dataRefs"):
            entry["targets"].append({"reference": reference.Identity, "operand": operand.Identity, "class": operand.ClassName, "body_ids": [body.Identity for body in LinkedNodes(graph, operand, "refBodies")]})
    entry["created_bodies"] = [body.Identity for body in LinkedNodes(graph, feature, "dcBodies")]
    return entry


parser = argparse.ArgumentParser()
parser.add_argument("source_directory", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
observations = args.source_directory / "CutCorpus.json"
if not observations.exists():
    observations = args.source_directory.parent / "NativeObservations.json"
captures = json.loads(observations.read_text())
report = {"scope": "research measurement of typed native planar journal states and operand joins; not a strict neutral decoder or native output acceptance", "cases": []}
for capture in captures["controls"]:
    path = args.source_directory / capture["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != capture["sha256"]:
        raise ValueError("Capture digest mismatch")
    model = ReadDocument(path.read_bytes())
    graph = BuildGraph(model)
    _, features = OrderedFeatures(graph, graph.OneClass("FusionComponent"))
    history = model.Bodies[0].History
    if not isinstance(history, JournalModel):
        report["cases"].append({"name": capture["name"], "sha256": capture["sha256"], "role": "healthy_native_control", "history_type": type(history).__name__})
        continue
    traces = [feature_trace(graph, feature) for feature in features]
    states = [measure(history, feature.Fields["endModelHS"]) for feature in features if feature.ClassName == "DcExtrudeFeature"]
    final = states[-1]
    expected = capture["observed"]["bodies"][0]
    matches = {key: math.isclose(final[key], expected[key], rel_tol=1e-9, abs_tol=1e-9) for key in ("volume_cm3", "area_cm2", "faces", "edges", "vertices")}
    matches.update({key: all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(final[key], expected[key], strict=True)) for key in ("min_cm", "max_cm")})
    report["cases"].append({"name": capture["name"], "sha256": capture["sha256"], "features": traces, "states": states, "native_measurement_match": matches, "strict_neutral_status": "not_implemented"})
    print(capture["name"], json.dumps(matches), flush=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
