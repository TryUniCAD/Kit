from TraceOffset import trace_offset
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
    moment = [0.0, 0.0, 0.0]
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
        for index in range(1, len(ring) - 1):
            tetra = DotProduct(ring[0], CrossProduct(ring[index], ring[index + 1])) / 6
            volume += tetra
            for axis in range(3):
                moment[axis] += tetra * (ring[0][axis] + ring[index][axis] + ring[index + 1][axis]) / 4
        rings.append(ring)
    return {"centroid_cm": [value / volume for value in moment], "state_id": table.StateId, "volume_cm3": volume, "area_cm2": area, "faces": len(faces), "edges": len(edges), "vertices": len(vertices), "min_cm": [min(point[axis] for point in points.values()) for axis in range(3)], "max_cm": [max(point[axis] for point in points.values()) for axis in range(3)], "rings_cm": rings}


parser = argparse.ArgumentParser()
parser.add_argument("source_directory", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
manifest = args.source_directory / "OffsetCorpus.json"
if not manifest.exists():
    manifest = args.source_directory.parent / "NativeObservations.json"
captures = {case["name"]: case for case in json.loads(manifest.read_text())["controls"]} if manifest.exists() else {}
report = {"scope": "typed source offset feature and native journal inspection; no strict neutral or native conversion acceptance", "cases": []}
for path in sorted(args.source_directory.glob("*.f3d")):
    if not any(word in path.stem.lower() for word in ("offset", "top", "side", "healthy")):
        continue
    case = {"name": path.stem, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    try:
        model = ReadDocument(path.read_bytes())
        graph = BuildGraph(model)
        _, features = OrderedFeatures(graph, graph.OneClass("FusionComponent"))
        case["features"] = [{"class": feature.ClassName, "id": feature.Identity, "fields": {key: repr(value) for key, value in feature.Fields.items()}} for feature in features]
        case["parameters"] = [{"class": node.ClassName, "id": node.Identity, "fields": {key: repr(value) for key, value in node.Fields.items()}} for node in graph.Nodes.values() if "Parameter" in node.ClassName and node.SegmentId == 0]
        case["target_records"] = [{"class": node.ClassName, "id": node.Identity, "fields": {key: repr(value) for key, value in node.Fields.items()}} for node in graph.Nodes.values() if node.SegmentId == 0 and (node.ClassName.startswith("DR") or "Ref" in node.ClassName or node.ClassName in ("ModelDataRef", "BodyProgenitor", "ASMRecipe", "BRepHistorySerializer"))]
        history = model.Bodies[0].History
        case["history_type"] = type(history).__name__
        if isinstance(history, JournalModel):
            case["offset_intents"] = [trace_offset(graph, feature, history) for feature in features if feature.ClassName == "DcOffsetFacesFeature"]
            case["journal_current_state"] = history.Stream.CurrentStateId
            case["states"] = [measure(history, state) for state in sorted({feature.Fields["endModelHS"] for feature in features if type(feature.Fields.get("endModelHS")) is int and feature.Fields["endModelHS"] >= 0})]
            case["current"] = measure(history, history.Stream.CurrentStateId)
            for intent in case["offset_intents"]:
                before = measure(history, intent["start_state"])
                after = measure(history, intent["end_state"])
                lower, upper = list(before["min_cm"]), list(before["max_cm"])
                axis = intent["axis"]
                side = upper if intent["outward_normal"][axis] > 0 else lower
                side[axis] += intent["distance_cm"] * intent["outward_normal"][axis]
                widths = [b - a for a, b in zip(lower, upper, strict=True)]
                if min(widths) <= 0 or before["faces"] != 6 or after["faces"] != 6:
                    raise ValueError("Research offset prediction requires one noncollapsed box")
                predictions = {"volume_cm3": math.prod(widths), "area_cm2": 2 * (widths[0]*widths[1] + widths[0]*widths[2] + widths[1]*widths[2]), "centroid_cm": [(a+b)/2 for a,b in zip(lower, upper, strict=True)], "min_cm": lower, "max_cm": upper}
                matches = {key: math.isclose(value, after[key], rel_tol=1e-9, abs_tol=1e-9) if isinstance(value, float) else all(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9) for a,b in zip(value, after[key], strict=True)) for key,value in predictions.items()}
                intent["box_rule_matches"] = matches
                if not all(matches.values()):
                    raise ValueError("Signed face recipe does not predict the final journal")
        capture = captures.get(path.stem)
        if capture and "current" in case:
            if capture["sha256"] != case["sha256"] or capture["status"] != "captured":
                raise ValueError("Native observation custody or capture failed")
            measured = capture["observed"]["bodies"][0]
            current = case["current"]
            comparisons = {key: math.isclose(current[key], measured[key], rel_tol=1e-9, abs_tol=1e-9) for key in ("volume_cm3", "area_cm2", "faces", "edges", "vertices")}
            comparisons.update({key: all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(current[key], measured[key], strict=True)) for key in ("centroid_cm", "min_cm", "max_cm")})
            case["native_measurement_match"] = comparisons
            if not all(comparisons.values()):
                raise ValueError("Decoded journal differs from native observations")
        case["status"] = "inspected"
    except Exception as error:
        case["status"] = "inspection_refused"
        case["error"] = str(error)
    report["cases"].append(case)
    print(case["name"], case["status"], case.get("error", ""), flush=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
