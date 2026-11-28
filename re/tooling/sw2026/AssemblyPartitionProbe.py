from __future__ import annotations

import json
import math
import subprocess
import sys
from base64 import b64decode
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from itertools import product
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(directory))

from convert import open_document
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.Models.GeometryCurves import LineGeometry
from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput

CASES = (
    ("OffsetRepeated", (2.8, -6.1, 21.3, 18.7, 16.7), True),
    ("CenteredSingle", (-18.8, -10.7, 18.8, 10.7, 10.9), False),
    ("L1Single", (-20.0, -10.0, 20.0, 10.0, 10.0), False),
)
CHILD = "PartitionProbeChild.SLDPRT"
WORKER = Path(__file__).with_name("AssemblyPartitionProcess.py")


def vector(value):
    return (value.x, value.y, value.z)


def close(actual, expected):
    return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-10)


def match(actual, expected):
    return len(actual) == len(expected) and all(close(a, b) for a, b in zip(actual, expected, strict=True))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def minus(a, b):
    return tuple(x-y for x, y in zip(a, b, strict=True))


def polyhedron(model, dimensions, body_id):
    left, bottom, right, top, depth = dimensions
    corners = tuple(product((left, right), (bottom, top), (0.0, depth)))
    counts = dict(curves=12, surfaces=6, vertices=8, edges=12, coedges=24, loops=6, faces=6,
                  face_uses=6, shells=1, shell_uses=1, regions=1, bodies=1)
    require(model is not None and not model.validate(frozenset((body_id,))), "decoded prism topology did not validate")
    require(all(len(getattr(model, name)) == count for name, count in counts.items()), "prism count differs")
    require(model.regions[0].solid and model.shells[0].closed and not (model.pcurves or model.wires), "prism is not a closed solid")
    vertices = {vertex.id: vector(vertex.point) for vertex in model.vertices}
    by_corner = {vertex: [i for i, corner in enumerate(corners) if match(point, corner)] for vertex, point in vertices.items()}
    require(all(len(indices) == 1 for indices in by_corner.values()) and len({entry[0] for entry in by_corner.values()}) == 8,
            "prism vertices do not match the eight independent box corners")
    edges = {edge.id: edge for edge in model.edges}
    curves = {curve.id: curve for curve in model.curves}
    edge_corner_pairs = set()
    for edge in edges.values():
        curve = curves[edge.curve_id]
        require(isinstance(curve, LineCurve) and not edge.degenerate, "box edge is not an exact straight segment")
        first, second = (vertices[key] for key in (edge.start_vertex_id, edge.end_vertex_id))
        require(sum(not close(a, b) for a, b in zip(first, second, strict=True)) == 1, "box edge changes multiple coordinate axes")
        edge_corner_pairs.add(tuple(sorted((by_corner[edge.start_vertex_id][0], by_corner[edge.end_vertex_id][0]))))
        for value, point in ((edge.start_parameter, first), (edge.end_parameter, second)):
            require(match(tuple(x + value*y for x, y in zip(vector(curve.origin), vector(curve.direction), strict=True)), point), "edge trim does not land on its endpoint")
    require(len(edge_corner_pairs) == 12, "box edges repeat a pair of corners")
    loops = {loop.id: loop for loop in model.loops}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    surfaces = {surface.id: surface for surface in model.surfaces}
    uses, plane_keys = Counter(), set()
    face_areas, tetrahedra = [], []
    centre = ((left + right)/2, (bottom + top)/2, depth/2)
    for face in model.faces:
        loop_id, = face.loop_ids
        loop = loops[loop_id]
        surface = surfaces[face.surface_id]
        require(loop.outer and len(loop.coedge_ids) == 4 and isinstance(surface, PlaneSurface), "box face lacks a planar quad boundary")
        directed_edges = []
        for key in loop.coedge_ids:
            coedge = coedges[key]
            edge = edges[coedge.edge_id]
            uses[edge.id, coedge.reversed] += 1
            pair = (edge.start_vertex_id, edge.end_vertex_id)
            directed_edges.append(pair[::-1] if coedge.reversed else pair)
        require(all(pair[1] == following[0] for pair, following in zip(directed_edges, directed_edges[1:]+directed_edges[:1], strict=True)), "face coedges do not form a continuous boundary")
        points = tuple(vertices[pair[0]] for pair in directed_edges)
        normal = vector(surface.normal)
        axis, = [i for i, value in enumerate(normal) if close(abs(value), 1.0)]
        plane_keys.add((axis, points[0][axis] > centre[axis]))
        require(all(close(dot(normal, minus(point, vector(surface.origin))), 0.0) for point in points), "face boundary is off its surface")
        for a, b in zip(points[1:-1], points[2:], strict=True):
            oriented = cross(minus(a, points[0]), minus(b, points[0]))
            require(dot(oriented, minus(points[0], centre)) > 0, "box boundary orientation points inward")
            face_areas.append(math.sqrt(dot(oriented, oriented))/2)
            signed = dot(points[0], cross(a, b))/6
            tetrahedra.append((signed, tuple((p+q+r)/4 for p, q, r in zip(points[0], a, b, strict=True))))
    require(len(plane_keys) == 6 and uses == Counter({(edge, rev): 1 for edge in edges for rev in (True, False)}),
            "box boundary lacks a unique oriented use on each edge side")
    volume = math.fsum(signed for signed, _ in tetrahedra)
    area = math.fsum(face_areas)
    centroid = tuple(math.fsum(signed * point[i] for signed, point in tetrahedra)/volume for i in range(3))
    width, height = right-left, top-bottom
    require(close(volume, width*height*depth) and close(area, 2*(width*height + width*depth + height*depth)) and match(centroid, centre),
            "measured topology contradicts independent prism measures")
    return {"counts": counts, "volume_mm3": volume, "area_mm2": area, "centre_mm": centroid,
            "bounds_mm": [[min(axis) for axis in zip(*vertices.values())], [max(axis) for axis in zip(*vertices.values())]]}


def neutral(case, dimensions, repeat, guest):
    left, bottom, right, top, depth = (value / 1000 for value in dimensions)
    request = MakeOccInput(case, [0, 0, 0], [1, 0, 0], [0, 1, 0])
    request["assembly"]["output"]["path_name"] = str(guest / (case + ".SLDASM"))
    request["child"] = MakeTreeInput(request["child"])
    request["child"]["output"]["path_name"] = str(guest / CHILD)
    request["child"]["document"].update(
        name=Path(CHILD).stem, configuration_name="Default", depth_m=depth,
        vertices_m=[[left, bottom], [right, bottom], [right, top], [left, top]],
        rectangle_dimensions={"width_text_m": [(left+right)/2, bottom-.004],
                              "height_text_m": [right+.004, (bottom+top)/2], "route_centerline": False},
    )
    request["occurrences"][0]["name"] = Path(CHILD).stem + "-1"
    if repeat:
        request["occurrences"].append({"name": Path(CHILD).stem + "-2", "placement": {
            "origin": [.0723, -.0531, .0315], "u": [0, 0, -1], "v": [0, 1, 0],
        }})
    return request


def read_history(child, before, expected, dimensions, child_path):
    sketch_id, extrusion_id = expected["sketch_id"], expected["extrusion_id"]
    feature_id = f"sldprt:feature:{extrusion_id}"
    sketch, = child.sketches
    feature = next(step for step in child.feature_timeline if step.id == feature_id)
    require(child.feature_timeline == before.feature_timeline and child.sketches == before.sketches and child.parameters == before.parameters,
            "cache changed the independent SDK history read")
    require(sketch.id == f"sldprt:sketch:{sketch_id}" and feature.sketch_id == sketch.id
            and feature.input_feature_ids == (f"sldprt:feature:{sketch_id}",)
            and str(feature.operation) == "join" and str(feature.definition.end_condition) == "blind"
            and child.bodies[0].final_feature_id == feature_id and not feature.definition.reversed,
            "SDK history does not preserve the generated sketch/boss/body relationship")
    left, bottom, right, top, depth = dimensions
    wanted = {f"sldprt:parameter:{sketch_id}:D1": right-left, f"sldprt:parameter:{sketch_id}:D2": top-bottom,
              f"sldprt:parameter:{extrusion_id}:D1": depth}
    actual = {p.id: p.value.value for p in child.parameters}
    require(actual.keys() == wanted.keys() and all(close(actual[key], number) for key, number in wanted.items())
            and close(feature.definition.length.value, depth), "SDK dimension values contradict rectangle input")
    line_ends = {(line.geometry.start.x, line.geometry.start.y, line.geometry.end.x, line.geometry.end.y)
                 for line in sketch.entities if isinstance(line.geometry, LineGeometry)}
    expected_edges = ((left,bottom,right,bottom), (right,bottom,right,top), (right,top,left,top), (left,top,left,bottom))
    require(len(line_ends) == 4 and all(any(match(a, b) for a in line_ends) for b in expected_edges), "SDK sketch lost a real rectangle edge")
    summary_box = child.bodies[0].topology.bounding_box
    archive = SldprtArchive.open(child_path)
    native, = NativePartModel(archive, "Default").sketches
    constraints = {c.parameter_id: str(c.kind) for c in sketch.constraints if c.parameter_id}
    endpoints = {c.parameter_id: [(ref.entity_id, ref.point) for ref in c.references]
                 for c in sketch.constraints if c.parameter_id and c.driving and not c.suppressed}
    expected_endpoints = {f"sldprt:parameter:{sketch_id}:D{index}":
                          [(f"{sketch.id}:line:{index}", "start"), (f"{sketch.id}:line:{index}", "end")]
                          for index in (1, 2)}
    profile_sizes = [len(loop) for loop in sketch.closed_profile_entity_ids]
    return {
        "unchanged_by_cache": True, "sketch_id": sketch.id, "support_plane_id": sketch.support_plane_id,
        "extrusion_id": feature.id, "design_body_id": child.bodies[0].id, "three_driving_values_mm": actual,
        "sketch_profiles": [{"kind": p.kind, "coordinates_mm": p.coordinates, "marker_offsets": p.marker_offsets,
                             "parameter": p.parameter_name, "dimension_kind": p.dimension_kind} for p in native.profiles],
        "sdk_entities": [str(entity.kind) for entity in sketch.entities], "closed_profile_sizes": profile_sizes,
        "dimension_constraints": constraints, "dimension_endpoints": endpoints,
        "summary_bounds_mm": (vector(summary_box.minimum), vector(summary_box.maximum)),
        "strict_sketch_semantics": len(sketch.entities) == 4 and profile_sizes == [4] and constraints == {
            f"sldprt:parameter:{sketch_id}:D1": "distance", f"sldprt:parameter:{sketch_id}:D2": "distance",
        } and endpoints == expected_endpoints,
        "strict_summary_bounds": match(vector(summary_box.minimum), (left,bottom,0.0)) and match(vector(summary_box.maximum), (right,top,depth)),
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def check_present_empty_cache(child_path):
    archive = SldprtArchive.open(child_path)
    require(KPartitionStream not in archive.streams, "the cold control already has a partition")
    streams = archive.streams | {KPartitionStream: b""}
    contrast = BuildSldprt(streams, FileId=archive.file_id, FormatVersion=archive.format_version)
    require(SldprtArchive.from_bytes(contrast).streams == streams, "the present empty partition changed another stream")
    try:
        open_document(contrast, source_format="solidworks.sldprt")
    except SldprtFormatError as error:
        require(str(error) == "SLDPRT contains no readable Parasolid payload", str(error))
        return str(error)
    raise ValueError("a present empty partition unexpectedly qualified as an absent cache")


def cold_geometry(parent_path, child_path, baseline, expected, dimensions, expected_sha):
    parent = open_document(parent_path)
    standalone = open_document(child_path)
    require(not parent.validate() and parent.assembly is not None, "cold assembly did not validate")
    linked, = parent.assembly.documents
    child = linked.document
    require(child.source.sha256 == standalone.source.sha256 == expected_sha,
            "cold assembly and standalone reads did not use the same generated child")
    require(child.brep is not None and child.brep == standalone.brep
            and not child.brep_payloads and not standalone.brep_payloads,
            "cold child did not expose reconstructed geometry without a kernel payload")
    body, = child.bodies
    require(len(child.brep.bodies) == 1 and child.brep.bodies[0].design_body_id == body.id,
            "cold geometry did not retain its actual design body")
    notice, = (entry for entry in child.diagnostics if entry.code == "sldprt.brep_reconstructed")
    require(notice.attributes["method"] == "typed_parametric_rectangular_prism"
            and notice.attributes["native_kernel_identity"] is False,
            "cold geometry lost its exact reconstruction method")
    observed = polyhedron(child.brep, dimensions, body.id)
    feature_id = f"sldprt:feature:{expected['extrusion_id']}"
    step, = (value for value in child.feature_timeline if value.id == feature_id)
    predecessor, = (value for value in baseline.feature_timeline if value.id == feature_id)
    require(str(step.operation) == "create" and str(predecessor.operation) == "join",
            "the first cold boss did not retain its independently bound create operation")
    compatible = tuple(replace(value, operation=predecessor.operation) if value is step else value
                       for value in child.feature_timeline)
    require(compatible == baseline.feature_timeline and child.sketches == baseline.sketches
            and child.parameters == baseline.parameters and body.final_feature_id == feature_id,
            "cold reconstruction changed the independent sketch or editable history")
    require(body.topology.valid is True and close(body.topology.volume, observed["volume_mm3"])
            and close(body.topology.surface_area, observed["area_mm2"]),
            "cold summary does not match its independent geometry")
    return observed


def inspect_case(stage, guest, case, dimensions, repeat):
    request = neutral(case, dimensions, repeat, guest)
    run = subprocess.run((sys.executable, "-B", str(WORKER)), input=json.dumps(request), capture_output=True, text=True, check=False)
    require(run.returncode == 0, run.stderr)
    result = json.loads(run.stdout)
    folder = stage / case
    folder.mkdir()
    parent = result["parent"]
    files = {}
    for name, key in (("WithoutPartition", "child_baseline"), ("WithPartition", "child_with_partition")):
        slot = folder / name
        slot.mkdir()
        paths = (slot / (case+".SLDASM"), slot / CHILD)
        for path, artifact in zip(paths, (parent, result[key]), strict=True):
            path.write_bytes(b64decode(artifact["base64"], validate=True))
            require(sha256(path.read_bytes()).hexdigest() == artifact["sha256"], "emitted file hash differs")
        files[name] = paths
    for artifact in (parent, result["child_baseline"], result["child_with_partition"]):
        del artifact["base64"]
    source_parent, cold_path = files["WithoutPartition"]
    baseline = open_document(source_parent, include_brep=False)
    require(baseline.assembly is not None, "design-only assembly geometry control failed")
    baseline_child = baseline.assembly.documents[0].document
    result["reconstructed_brep"] = cold_geometry(
        source_parent, cold_path, baseline_child, result["geometry"], dimensions, result["child_baseline"]["sha256"]
    )
    result["present_empty_partition_error"] = check_present_empty_cache(cold_path)
    parent_path, child_path = files["WithPartition"]
    sdk = open_document(parent_path)
    child_alone = open_document(child_path)
    require(not (sdk.validate() or child_alone.validate() or baseline.validate()) and sdk.assembly is not None, "default SDK model did not validate")
    require(len(sdk.assembly.instances) == len(request["occurrences"]) and len(sdk.assembly.definitions) == 2
            and len(sdk.assembly.documents) == 1 and len({occurrence.definition_id for occurrence in sdk.assembly.instances}) == 1,
            "assembly does not preserve the shared child and occurrence count")
    for instance, occurrence in zip(sdk.assembly.instances, request["occurrences"], strict=True):
        placement = occurrence["placement"]
        u, v, point = placement["u"], placement["v"], (1, 2, 3)
        delta = cross(u, v)
        projected = (u[i]*point[0] + v[i]*point[1] + delta[i]*point[2] + placement["origin"][i]*1000 for i in range(3))
        require(instance.name == occurrence["name"] and match(instance.transform.TransformPoint(point), tuple(projected)), "assembly instance placement differs")
    child = sdk.assembly.documents[0].document
    require(child.brep == child_alone.brep and child.source.sha256 == result["child_with_partition"]["sha256"]
            and len(child.brep_payloads) == 1 and child.brep_payloads[0].sha256 == result["partition"]["decoded_sha256"],
            "linked child read did not use the generated partition")
    result["measured_brep"] = polyhedron(child.brep, dimensions, child.bodies[0].id)
    result["history"] = read_history(child, baseline_child, result["geometry"], dimensions, child_path)
    result["sdk_document_valid"] = True
    result["native_oracle_run"] = False
    result["guest_active_path"] = str(guest)
    write_json(folder / "Neutral.json", request)
    write_json(folder / "Receipt.json", result)
    return {"name": case, "receipt_sha256": sha256((folder / "Receipt.json").read_bytes()).hexdigest(),
            "neutral_sha256": sha256((folder / "Neutral.json").read_bytes()).hexdigest(),
            "sdk_strict_cacheless_geometry": True,
            "present_empty_partition_error": result["present_empty_partition_error"],
            "sdk_strict_sketch_semantics": result["history"]["strict_sketch_semantics"],
            "sdk_strict_summary_bounds": result["history"]["strict_summary_bounds"]}


if __name__ == "__main__":
    stage = Path(sys.argv[1]).resolve()
    require(not stage.is_relative_to(ROOT), "stage generated archives outside the repository")
    stage.mkdir(mode=0o700, exist_ok=False)
    guest = PureWindowsPath("C:/Users/Public/Documents/KitOracle") / stage.name / "Active"
    cases = [inspect_case(stage, guest / case, case, dimensions, repeat) for case, dimensions, repeat in CASES]
    write_json(stage / "Index.json", {"schema": "kit.sw2026.generated-assembly-partition-probe.v2", "cases": cases})
    print(stage / "Index.json")
