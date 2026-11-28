from __future__ import annotations

from dataclasses import replace
import importlib.util
import math
from pathlib import Path
import re
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def number(value, label, positive=False):
    require(type(value) in (int, float) and math.isfinite(value), label + " must be finite")
    require(not positive or value > 0, label + " must be positive")
    return float(value)


def project_spec(case):
    allowed = {"name", "split", "plane", "profile", "depth_mm", "reverse", "dimension_kind", "end_condition",
               "reverse_depth_mm", "expected_bodies", "edit", "export_siblings", "creation"}
    require(type(case) is dict and not set(case) - allowed, "unqualified source case fields: " + repr(set(case) - allowed))
    require(type(case.get("name")) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", case["name"]), "source name must be a safe independent identity")
    require(case.get("split") in ("heldout", "discovery"), "source split is not an admitted model input")
    require(case.get("plane") in ("front", "top", "right"), "source support is not a canonical principal frame")
    require(type(case.get("reverse")) is bool, "source reversal must be explicit")
    require(type(case.get("expected_bodies")) is int and case["expected_bodies"] == 1, "source requires one actual intended solid")
    require(case.get("creation") in (None, "point-circle-control"), "source creation ownership needs separate qualification")
    if "export_siblings" in case:
        require(type(case["export_siblings"]) is bool, "sibling export policy is not boolean")
    profile = case.get("profile")
    require(type(profile) is dict and not set(profile) - {"kind", "center_mm", "radius_mm", "construction_arcs"}, "source profile carries unqualified geometry")
    require(profile.get("kind") == "circle" and not profile.get("construction_arcs", []), "source is not one ordinary closed circle")
    center = profile.get("center_mm")
    require(type(center) is list and len(center) == 2, "source circle needs both local centre coordinates")
    center = tuple(number(value, "circle centre") for value in center)
    radius = number(profile.get("radius_mm"), "circle radius", True)
    depth = number(case.get("depth_mm"), "primary depth", True)
    mode = {"radial": "radius", "radius": "radius", "diameter": "diameter"}.get(case.get("dimension_kind", "radial"))
    require(mode is not None, "source radial driving intent is unsupported")
    condition = case.get("end_condition", "blind")
    require(condition in ("blind", "mid_plane", "two_directions"), "source end owner is unsupported")
    second = case.get("reverse_depth_mm", 0.0)
    if condition == "two_directions":
        second = number(second, "second depth", True)
    else:
        require(number(second, "inactive second depth") == 0.0, "single end carries another active depth")
        second = None
    edit = case.get("edit")
    require(type(edit) is dict and set(edit) == {"target", "factor"}, "source edit intent is not fully classified")
    require(edit["target"] in ("curve-0", "depth", "reverse-depth"), "source edit target is unsupported")
    factor = number(edit["factor"], "source edit factor", True)
    require(factor != 1 and (edit["target"] != "reverse-depth" or second is not None), "source edit cannot be exercised")
    return {"name": case["name"], "plane": case["plane"], "center_mm": center, "radius_mm": radius,
            "depth_mm": depth, "mode": mode, "end_condition": condition, "reverse": case["reverse"],
            "second_mm": second, "source_edit": dict(edit), "configuration_name": "Default",
            "sketch_name": "CurveSketch", "feature_name": "CurveBoss",
            "radial_edit_factor": factor if edit["target"] == "curve-0" else 1.137,
            "depth_edit_factor": factor if edit["target"] == "depth" else 0.823,
            "second_edit_factor": factor if edit["target"] == "reverse-depth" else 1.219}


def neutral_request(root, spec, created_at):
    root = Path(root).resolve()
    sys.path[:0] = [str(root / "src"), str(root)]
    path = root / "re/tooling/sw2026/AuthorSdkCircleRequests.py"
    module_spec = importlib.util.spec_from_file_location("sdk_circle_independent_neutral", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    from interchange.Features.FeatureExtrude import ExtrudeEnd
    from interchange.serialization.EncodeData import ToData
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    conditions = {"blind": ExtrudeEnd.KBlind, "mid_plane": ExtrudeEnd.KMidPlane, "two_directions": ExtrudeEnd.KTwoLengths}
    document = module.make_document(spec["name"], {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}[spec["plane"]],
                                    spec["center_mm"], spec["radius_mm"], spec["depth_mm"], spec["mode"],
                                    conditions[spec["end_condition"]], spec["reverse"], spec["second_mm"])
    document = replace(document, configurations=(replace(document.configurations[0], name=spec["configuration_name"]),),
                       sketches=(replace(document.sketches[0], name=spec["sketch_name"]),),
                       feature_timeline=(replace(document.feature_timeline[0], name=spec["feature_name"]),),
                       bodies=(replace(document.bodies[0], name=spec["feature_name"]),))
    document.assert_valid()
    system = MakePartRecipe(ProjectCircle(document), created_at).SystemValue
    result = {"document": ToData(document), "created_at": created_at,
              "radial_edit_factor": spec["radial_edit_factor"], "depth_edit_factor": spec["depth_edit_factor"],
              "expected_system": {"folders": system.FolderValues, "planes": dict(system.PlaneNames),
                                  "cabinet_name": system.CabinetName, "origin_name": system.OriginName}}
    if spec["second_mm"] is not None:
        result["second_edit_factor"] = spec["second_edit_factor"]
    return result


def expected_tree(spec, system):
    rows = []
    for tag, name in system["folders"]:
        rows.append([name, tag.removeprefix("mo").removesuffix("_c"), None])
        if tag == "moDocsFolder_c":
            cabinet = system["cabinet_name"]
            rows.extend(([cabinet, "DetailCabinet", None], ["Notes", "NotesAreaFtrFolder", cabinet],
                         ["Notes1___EndTag___", "NotesAreaFtrFolder", cabinet]))
        if tag == "moEnvFolder_c":
            rows.append(["Ambient", "AmbientLight", name])
            rows.extend([f"Directional{index}", "DirectionLight", name] for index in range(1, 4))
    rows.extend([system["planes"][axis], "RefPlane", None] for axis in ("z", "y", "x"))
    rows.extend(([system["origin_name"], "OriginProfileFeature", None], [spec["sketch_name"], "ProfileFeature", None],
                 [spec["feature_name"], "Extrusion", None]))
    require(len(rows) == 25, "ordinary authored system tree is not fully classified")
    return rows


def frame(plane):
    return {"front": ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)),
            "right": ((0., 0., -1.), (0., 1., 0.), (1., 0., 0.)),
            "top": ((1., 0., 0.), (0., 0., -1.), (0., 1., 0.))}[plane]


def analytic(spec, radial=1.0, depth=1.0, second=1.0):
    radius = spec["radius_mm"] * radial * 0.001
    length = spec["depth_mm"] * depth * 0.001
    other = 0.0 if spec["second_mm"] is None else spec["second_mm"] * second * 0.001
    low, high = (-length / 2, length / 2) if spec["end_condition"] == "mid_plane" else (-other, length)
    if spec["reverse"]:
        low, high = -high, -low
    basis = frame(spec["plane"])
    center = [value * 0.001 for value in spec["center_mm"]]
    world = [sum(center[j] * basis[j][i] for j in range(2)) for i in range(3)]
    midpoint = (low + high) / 2
    total = high - low
    bounds = []
    for axis in range(3):
        extent = radius * math.hypot(basis[0][axis], basis[1][axis])
        ends = [world[axis] + basis[2][axis] * value for value in (low, high)]
        bounds.append((min(ends) - extent, max(ends) + extent))
    return {"volume_m3": math.pi * radius * radius * total,
            "area_m2": 2 * math.pi * radius * (radius + total),
            "com_m": [world[i] + basis[2][i] * midpoint for i in range(3)],
            "bounds_m": bounds, "axial_interval_m": [low, high]}
