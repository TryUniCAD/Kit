from __future__ import annotations

import math
from pathlib import PureWindowsPath

from AuthorCurves import require
from PredictSdkNestedAssembly import part_geometry, predict
from PrepareSdkAssemblyNative import tree_rows


SCHEMA = "kit.sw2026.sdk-nested-independent-prediction.v1"


def save_order(request):
    definitions = {row["id"]: row for row in request["definitions"]}
    order, active = [], set()

    def visit(key):
        require(key in definitions and key not in active, "invalid authored dependency graph")
        if key in order:
            return
        active.add(key)
        row = definitions[key]
        for occurrence in row.get("occurrences", ()):
            visit(occurrence["target"])
        order.append(key)
        active.remove(key)

    visit(request["root"])
    require(len(order) == len(definitions), "native prediction requires the complete reachable dependency closure")
    return order


def expected_trees(request):
    part = next(row["request"] for row in request["definitions"] if row["kind"] == "part")
    assembly = next(row["request"] for row in request["definitions"] if row["kind"] == "assembly")
    trees = {}
    for row in request["definitions"]:
        adapted = {"assembly": row["request"] if row["kind"] == "assembly" else assembly,
                   "child": row["request"] if row["kind"] == "part" else part,
                   "occurrences": [item["occurrence"] for item in row.get("occurrences", ())], "mate": {"name": "unused"}}
        tree = tree_rows(adapted)
        if row["kind"] == "assembly":
            trees[row["id"]] = tree["parent"][:-1]
        else:
            document = row["request"]["document"]
            sketch, = document["sketches"]["$tuple"]
            feature, = document["feature_timeline"]["$tuple"]
            tree["child"][-2][0], tree["child"][-1][0] = sketch["name"], feature["name"]
            trees[row["id"]] = tree["child"]
    return trees


def prediction(request, edit_part, edit_depth_m):
    definitions = {row["id"]: row for row in request["definitions"]}
    require(edit_part in definitions and definitions[edit_part]["kind"] == "part"
            and type(edit_depth_m) in (int, float) and math.isfinite(edit_depth_m) and edit_depth_m > 0,
            "the native trial requires an explicit positive depth edit on an authored leaf")
    initial = predict(request)
    require(edit_depth_m != initial["parts"][edit_part]["depth_m"], "the native edit must change the authored depth")
    edited = predict(request, edit_part=edit_part, edit_depth=edit_depth_m)
    targets = {}
    for key, row in definitions.items():
        if row["kind"] == "part":
            before = part_geometry(row["request"])
            after = part_geometry(row["request"], edit_depth_m if key == edit_part else None)
            config = before["configuration"]
            path = row["request"]["settings"]["output"]["path_name"]
        else:
            local = dict(request, root=key)
            a, b = predict(local), predict(local, edit_part=edit_part, edit_depth=edit_depth_m)
            before = a["assembly"] | {"body_count": a["body_count"]}
            after = b["assembly"] | {"body_count": b["body_count"]}
            config = row["request"]["configuration_name"]
            path = row["request"]["output"]["path_name"]
        targets[key] = {"kind": row["kind"], "file": PureWindowsPath(path).name, "encoded_path": path,
                        "configuration": config, "initial": before, "edited": after}
    feature, = definitions[edit_part]["request"]["document"]["feature_timeline"]["$tuple"]
    return {"schema": SCHEMA, "root": request["root"], "definitions": targets, "initial": initial, "edited": edited,
            "edit": {"part": edit_part, "parameter": "D1@" + feature["name"], "depth_m": edit_depth_m},
            "trees": expected_trees(request), "save_order": save_order(request), "writer_frames_or_readback_used": False,
            "source_observations_read": 0, "heldout_inputs_read": 0, "native_acceptance": False}


def verify_prediction(request, expected):
    require(prediction(request, expected["edit"]["part"], expected["edit"]["depth_m"]) == expected,
            "the frozen native prediction does not follow independently from its neutral definition DAG")
    paths = [PureWindowsPath(row["encoded_path"]) for row in expected["definitions"].values()]
    require(all(path.is_absolute() and path.name == row["file"] for path, row in zip(paths, expected["definitions"].values(), strict=True))
            and len({str(path).casefold() for path in paths}) == len(paths) and len({path.parent for path in paths}) == 1,
            "the generated native bundle must use distinct files in one exact owned working directory")
    require(expected["initial"]["expanded_occurrences"] >= 2
            and expected["initial"]["assembly"]["volume"] != expected["edited"]["assembly"]["volume"],
            "the authored leaf edit must change the independently predicted root geometry")
    return paths[0].parent
