from __future__ import annotations

from hashlib import sha256
import json
from pathlib import PureWindowsPath
import re

from AuthorCurves import require
from ReferencePlaneSourcePlan import BASE_NAMES, BOSS, PLANE, SKETCH, geometry, validate_case


SCHEMA = "kit.sw2026.disclosed-offset-plane-recipe.v1"
AXES = {"right": "x", "top": "y", "front": "z"}
BASIS = {"right": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
         "top": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
         "front": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))}


def checked_case(case, *, heldout=False):
    validate_case(case)
    slots = ("H01", "H02") if heldout else ("D01", "D02", "D03", "D04")
    split = "heldout" if heldout else "discovery"
    require(case["id"] in slots and case["split"] == split, "the declared plane source slot differs from the recipe scope")
    return case


def source_request(case, working, *, heldout=False):
    from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput
    from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput

    checked_case(case, heldout=heldout)
    working = PureWindowsPath(working)
    require(working.is_absolute() and (re.fullmatch(r"[A-Za-z]:", working.drive) or working.drive.startswith("\\\\"))
            and ".." not in working.parts, "the disclosed recipe requires an absolute declared guest working path")
    request = MakeTreeInput(MakePartInput([], case["depth_m"], case["name"]))
    request["document"].pop("vertices_m")
    initial = geometry(case)
    u, v = BASIS[case["base"]]
    cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    require(cross == initial["normal"], "the authored principal frame must preserve its independently predicted normal")
    text = [initial["plane_origin"][index] + case["radius_m"] * (1.7 * u[index] + 1.3 * v[index]) for index in range(3)]
    request["document"].update(configuration_name="Default", profile_kind="circle", feature_kind="blind_extrusion",
                               sketch_name=SKETCH, extrusion_name=BOSS, origin_name="Origin", plane_axis=AXES[case["base"]],
                               center_m=[0.0, 0.0], radius_m=case["radius_m"],
                               circle_dimension={"mode": "radius", "text_point_m": text, "fix_center": True})
    request["presentation"]["folder_order"] = list(request["presentation"]["folder_names"])
    request["offset_plane_discovery"] = {"name": PLANE, "distance_m": case["distance_m"], "reverse": case["reverse"]}
    request["output"] = {"path_name": str(working / (case["name"] + ".SLDPRT")),
                         "saved_at": request["provenance"]["modified_at"] + 51}
    return request


def source_prediction(case, *, heldout=False):
    checked_case(case, heldout=heldout)
    principal = {"x": BASE_NAMES["right"], "y": BASE_NAMES["top"], "z": BASE_NAMES["front"]}
    native = {"name": case["name"], "configuration": "Default", "plane": PLANE, "sketch": SKETCH,
              "boss": BOSS, "origin": "Origin", "principal_names": principal, "base_axis": AXES[case["base"]],
              "base_name": BASE_NAMES[case["base"]], "reverse": case["reverse"],
              "geometry": {"initial": geometry(case), "edited": geometry(case, True)}}
    source_hash = sha256(json.dumps(case, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {"schema": SCHEMA, "case_id": case["id"], "authored_specification_sha256": source_hash,
            "native_observer_prediction": native, "edit_distance_m": case["edit_distance_m"],
            "ordered_semantic_features": [[BASE_NAMES[name], "RefPlane"] for name in ("front", "top", "right")]
                + [["Origin", "OriginProfileFeature"], [PLANE, "RefPlane"], [SKETCH, "ProfileFeature"], [BOSS, "Extrusion"]],
            "source_generated_full_ordered_tree_equality_required": True,
            "source_generated_exact_semantic_identity_required": True,
            "generated_initial_edit_reopen_full_tree_equality_required": True,
            "native_fields_or_observations_used_as_inputs": False, "native_acceptance": False,
            "heldout_execution_enabled": False}
