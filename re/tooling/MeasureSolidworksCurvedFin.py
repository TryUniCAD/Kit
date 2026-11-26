from argparse import ArgumentParser
from collections import Counter, defaultdict
from hashlib import sha256
from math import cos, dist, isclose, pi, radians, sin
from pathlib import Path, PureWindowsPath
from unittest.mock import patch
import json
import os
import sys


CASE = "H05RotatedCapsule"
SCHEMA = "SCH_3701250_37102_13006"
PUBLISHED_LOCK = "7773c393e60696c12a7a7202d294762dc5a7e35c25d1ea364201f59a8ee04c24"
RAW_LOCK = "21da3f3e8a6e2a6fe732f69c377a9539bc26a3ee1111795319b4a95d0124ad25"
SPECS = "514c6e5d39933b29b904a98400d980b361fc4cb92644e2e626cfec0236f0d7b0"
DECODER = "0dbe22a69f954fabc945f46931757e99179d1f562487f7b534da3cc6e796e2d9"
ADAPTER = "5f0d19ce0f955ac117bba9b7bd0be1d77dff2c5763ca00c81f0e84943da37dff"
TOLERANCE_MM = 1e-6


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_checked(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, f"unexpected hash for {path.name}")
    return data


def xyz(value):
    return (value.x, value.y, value.z)


def near(actual, expected):
    return isclose(actual, expected, rel_tol=2e-7, abs_tol=TOLERANCE_MM)


def arc_values(curve, start, end, lower, upper, ends, axis, radius):
    center = xyz(curve.center)
    index = min(range(len(ends)), key=lambda i: dist(center[:2], ends[i]))
    require(dist(center, (*ends[index], start[2])) <= TOLERANCE_MM, "arc center differs")
    require(near(curve.radius, radius), "arc radius differs")
    radius = curve.radius
    sign = curve.axis.z
    reference = curve.reference_direction
    require(near(dist(xyz(curve.axis), (0, 0, 0)), 1) and near(abs(sign), 1)
            and near(reference.z, 0) and near(dist(xyz(reference), (0, 0, 0)), 1),
            "invalid circular cap frame")

    def point(angle):
        return (center[0] + radius * (reference.x * cos(angle) - sign * reference.y * sin(angle)),
                center[1] + radius * (reference.y * cos(angle) + sign * reference.x * sin(angle)),
                center[2])

    require(dist(point(lower), start) <= TOLERANCE_MM and dist(point(upper), end) <= TOLERANCE_MM,
            "arc parameters do not follow both vertices")
    swept = upper - lower
    middle = point((upper + lower) / 2)
    side = sum((middle[i] - center[i]) * axis[i] for i in range(2))
    require(near(abs(swept), pi) and near(side, (-1 if index == 0 else 1) * radius),
            "arc trim does not traverse the outer semicircle")
    return swept * sign * radius**2 + center[0] * (end[1] - start[1]) - center[1] * (end[0] - start[0]), abs(swept) * radius


def measure(model, case):
    from interchange.brep.Curves.BrepCurves import CircleCurve, LineCurve
    from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface

    profile = case["profile"]
    radius, span, depth = profile["radius_mm"], profile["center_spacing_mm"], case["depth_mm"]
    center = tuple(profile["center_mm"])
    angle = radians(profile["rotation_deg"])
    axis = (cos(angle), sin(angle))
    normal = (-axis[1], axis[0])
    ends = tuple(tuple(center[i] + side * axis[i] * span / 2 for i in range(2)) for side in (-1, 1))
    corners = tuple(tuple(end[i] + side * normal[i] * radius for i in range(2))
                    for end in ends for side in (-1, 1))

    require(not model.validate(), "typed B-rep has validation errors")
    counts = {name: len(getattr(model, name)) for name in
              ("bodies", "regions", "shells", "faces", "loops", "coedges", "edges", "vertices")}
    require(tuple(counts.values()) == (1, 1, 1, 6, 6, 24, 12, 8), f"unexpected topology {counts}")
    require(model.regions[0].solid and model.shells[0].closed, "body is not a closed solid")
    require(len(model.shell_uses) == 1 and not model.shell_uses[0].reversed and len(model.face_uses) == 6
            and {use.face_id for use in model.face_uses if not use.reversed} == {face.id for face in model.faces},
            "shell does not cover each forward face")

    vertices = {vertex.id: xyz(vertex.point) for vertex in model.vertices}
    expected_vertices = [(*corner, z) for z in (0.0, depth) for corner in corners]
    require(all(sum(dist(actual, expected) <= TOLERANCE_MM for actual in vertices.values()) == 1
                for expected in expected_vertices), "capsule tangent vertices differ from authored positions")
    edges = {edge.id: edge for edge in model.edges}
    curves = {curve.id: curve for curve in model.curves}
    coedges = {use.id: use for use in model.coedges}
    loops = {loop.id: loop for loop in model.loops}
    surfaces = {surface.id: surface for surface in model.surfaces}
    orientations = defaultdict(list)
    caps = {}
    walls = Counter()
    for face in model.faces:
        (loop_id,) = face.loop_ids
        loop = loops[loop_id]
        require(loop.outer and len(loop.coedge_ids) == 4, "expected one four-use outer loop per face")
        surface = surfaces[face.surface_id]
        trace = []
        for use_id in loop.coedge_ids:
            use = coedges[use_id]
            edge = edges[use.edge_id]
            orientations[edge.id].append(use.reversed)
            start, end = edge.start_vertex_id, edge.end_vertex_id
            low, high = edge.start_parameter, edge.end_parameter
            if use.reversed:
                start, end, low, high = end, start, high, low
            trace.append((start, end, curves[edge.curve_id], low, high))
        require(all(item[1] == following[0] for item, following in zip(trace, trace[1:] + trace[:1])),
                "loop coedges do not connect in traversal order")
        cap_side = next((side for side, z in (("bottom", 0.0), ("top", depth))
                         if all(near(vertices[start][2], z) for start, _, _, _, _ in trace)), None)
        if cap_side is None:
            upright = [(vertices[start], vertices[end], curve) for start, end, curve, _, _ in trace
                       if not near(vertices[start][2], vertices[end][2])]
            rims = [(vertices[start][2], curve) for start, end, curve, _, _ in trace
                    if near(vertices[start][2], vertices[end][2])]
            require(len(upright) == 2 and len(rims) == 2
                    and all(dist(a[:2], b[:2]) <= TOLERANCE_MM and isinstance(curve, LineCurve)
                            for a, b, curve in upright)
                    and not near(rims[0][0], rims[1][0]), "wall is not a forward vertical extrusion")
            carried = [curve for _, curve in rims]
            if isinstance(surface, CylinderSurface):
                require(near(abs(surface.axis.z), 1) and near(surface.radius, radius)
                        and all(isinstance(curve, CircleCurve) and dist(xyz(curve.center)[:2], xyz(surface.origin)[:2]) <= TOLERANCE_MM
                                for curve in carried), "cylindrical wall does not carry the cap arcs")
                walls["cylinder"] += 1
            else:
                require(isinstance(surface, PlaneSurface) and near(surface.normal.z, 0)
                        and all(isinstance(curve, LineCurve) for curve in carried)
                        and all(near(sum((vertices[start][i] - xyz(surface.origin)[i]) * xyz(surface.normal)[i] for i in range(3)), 0)
                                for start, _, _, _, _ in trace), "plane wall does not carry the cap lines")
                walls["plane"] += 1
            continue

        require(cap_side not in caps and isinstance(surface, PlaneSurface)
                and near(abs(surface.normal.z), 1) and near(surface.origin.z, vertices[trace[0][0]][2]),
                "unexpected cap support")
        kinds = Counter()
        area = perimeter = 0.0
        for start_id, end_id, curve, low, high in trace:
            start, end = vertices[start_id], vertices[end_id]
            if isinstance(curve, CircleCurve):
                twice_area, length = arc_values(curve, start, end, low, high, ends, axis, radius)
                kinds["arcs"] += 1
            else:
                require(isinstance(curve, LineCurve) and near(dist(start, end), span)
                        and all(dist(tuple(x + t * d for x, d in zip(xyz(curve.origin), xyz(curve.direction))), p) <= TOLERANCE_MM
                                for t, p in ((low, start), (high, end))), "cap line traversal differs")
                twice_area = start[0] * end[1] - end[0] * start[1]
                length = dist(start, end)
                kinds["lines"] += 1
            area += twice_area / 2
            perimeter += length
        require(kinds == {"arcs": 2, "lines": 2}, "cap does not traverse two arcs and two lines")
        caps[cap_side] = {"z_mm": surface.origin.z, "signed_area_mm2": area, "perimeter_mm": perimeter, **kinds,
                          "outward_normal_z": surface.normal.z * (1 if face.same_sense else -1)}

    require(set(orientations) == set(edges) and all(sorted(pair) == [False, True] for pair in orientations.values()),
            "each closed-shell edge must have two opposing traversals")
    require(set(caps) == {"bottom", "top"} and walls == {"cylinder": 2, "plane": 2}, "capsule faces are incomplete")
    bottom, top = caps["bottom"], caps["top"]
    height = top["z_mm"] - bottom["z_mm"]
    signed_volume = (top["signed_area_mm2"] - bottom["signed_area_mm2"]) * height / 2
    surface_area = sum(abs(cap["signed_area_mm2"]) + cap["perimeter_mm"] * height / 2 for cap in caps.values())
    area = pi * radius**2 + 2 * radius * span
    perimeter = 2 * pi * radius + 2 * span
    expected = {"profile_area_mm2": area, "perimeter_mm": perimeter, "volume_mm3": area * depth,
                "surface_area_mm2": 2 * area + perimeter * depth, "centroid_mm": (*center, depth / 2)}
    passed = (near(height, depth) and near(bottom["signed_area_mm2"], -area) and near(top["signed_area_mm2"], area)
              and near(bottom["outward_normal_z"], -1) and near(top["outward_normal_z"], 1)
              and all(near(cap["perimeter_mm"], perimeter) for cap in caps.values())
              and near(signed_volume, expected["volume_mm3"]) and near(surface_area, expected["surface_area_mm2"]))
    return {"passed": passed, "topology": counts, "caps": caps, "walls": dict(walls), "height_mm": height,
            "signed_volume_mm3": signed_volume, "surface_area_mm2": surface_area, "expected": expected}


def evaluate(model, case):
    if model is None:
        return {"passed": False, "typed_brep": False}
    try:
        return {"typed_brep": True, **measure(model, case)}
    except (KeyError, TypeError, ValueError) as error:
        return {"passed": False, "typed_brep": True, "reason": str(error)}


def run(batch_dir, specs_path, published_lock_path):
    require(os.name == "nt", "read the original source inside the oracle guest")
    sdk = Path(__file__).resolve().parents[2] / "src"
    read_checked(sdk / "convert/Geometry/Parasolid.py", DECODER)
    read_checked(sdk / "convert/adapters/solidworks/Core/Adapter.py", ADAPTER)
    sys.path.insert(0, str(sdk))
    from convert import open_document
    from convert.Geometry import Parasolid

    lock = json.loads(read_checked(published_lock_path, PUBLISHED_LOCK))
    raw_lock = json.loads(read_checked(batch_dir / "Lock.json", RAW_LOCK))
    specs = json.loads(read_checked(specs_path, SPECS))
    (case,) = (entry for entry in specs["cases"] if entry["name"] == CASE)
    (freeze,) = (entry for entry in lock["cases"] if entry["name"] == CASE)
    (raw_freeze,) = (entry for entry in raw_lock["cases"] if entry["name"] == CASE)
    require(case["split"] == freeze["split"] == "heldout" and case["plane"] == "front"
            and not case["reverse"] and case["profile"]["kind"] == "capsule", "unexpected frozen authoring profile")
    relative = PureWindowsPath(lock["publication_provenance"]["original_file_paths_windows"][CASE])
    require(relative.as_posix() == freeze["file"] and relative == PureWindowsPath(raw_freeze["file"])
            and raw_freeze["sha256"] == freeze["sha256"] == "f2ed589c9405bc81dc5d76b99ab469a2a14818ab0967cbb4a44128e5ea6b0662",
            "original held-out locator or lock differs")
    source = batch_dir.joinpath(*relative.parts)
    read_checked(source.with_name("Manifest.json"), freeze["manifest_sha256"])
    original = read_checked(source, freeze["sha256"])
    document = open_document(original, source_format="solidworks.sldprt", strict=True,
                             include_brep=True, include_tessellation=False)
    require(document.source.sha256 == freeze["sha256"], "strict reader used different source bytes")
    matches = []
    for payload in document.brep_payloads:
        if payload.schema == SCHEMA and payload.data is not None and "delta" not in payload.kind.casefold():
            candidate = Parasolid.DecodeBrepModel(payload.data)
            if candidate is not None:
                matches.append((payload, candidate))
    result = {"schema": "kit.sw2026.heldout-capsule-fin.v1", "case": CASE, "source_sha256": freeze["sha256"],
              "manifest_sha256": freeze["manifest_sha256"], "raw_lock_sha256": RAW_LOCK,
              "authoring_specs_sha256": SPECS, "sdk_decoder_sha256": DECODER, "sdk_adapter_sha256": ADAPTER,
              "payload_schemas": sorted({payload.schema for payload in document.brep_payloads}),
              "original_author_build": ".".join(map(str, lock["oracle"]["file_version_words"])),
              "container_format_version": document.source.container_version, "matched_partitions": len(matches),
              "passed": False}
    if len(matches) == 1 and document.brep == matches[0][1]:
        payload, model = matches[0]
        result["partition"] = {"schema": payload.schema, "stream": payload.source_stream, "sha256": payload.sha256}
        result["current"] = evaluate(model, case)
        scan = Parasolid.ScanPartRecords
        with patch.object(Parasolid, "ScanPartRecords", lambda data, **_: scan(data, TerminalFinVertices=False)):
            control = Parasolid.DecodeBrepModel(payload.data)
        result["pre_fix_interpretation"] = evaluate(control, case)
        result["passed"] = result["current"]["passed"]
    else:
        result["reason"] = "strict SDK result does not come from one directly decoded current-schema partition"
    read_checked(source, freeze["sha256"])
    result["source_unchanged"] = True
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("batch_dir", type=Path)
    parser.add_argument("specs", type=Path)
    parser.add_argument("published_lock", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    result = run(args.batch_dir, args.specs, args.published_lock)
    with args.receipt.open("x", encoding="utf-8") as destination:
        json.dump(result, destination, sort_keys=True, indent=2, allow_nan=False)
        destination.write("\n")
    print(json.dumps({"passed": result["passed"], "case": CASE, "source_unchanged": result["source_unchanged"]}))
    raise SystemExit(0 if result["passed"] else 1)
