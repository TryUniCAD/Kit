from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath

import AuthorCurves as curves
from InspectFrontDrawingMap import phase
from InspectSdkBlindPart import tree_prediction
from InspectSdkLinkedDrawing import CONTROL_DRAWING, CONTROL_PART, ORACLE, TOOLS as LINKED_TOOLS, checked, observe_child


SCHEMA = "kit.sw2026.sdk-cached-child-drawing-native.v1"
TOOLS = (*LINKED_TOOLS, Path(__file__).name)
STEMS = {"drawing": "CachedChildDrawing.SLDDRW", "part": "CachedChildDrawingChild.SLDPRT"}


def read_json(path):
    return json.loads(path.read_bytes())


def geometry(states, x, y, depth):
    width, height = states
    return {
        "position_m": [x, y], "scale": 1.0,
        "model_to_view": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, x, y, -depth / 2, 1.0, 0.0, 0.0, 0.0],
        "child_volume_m3": width * height * depth,
        "child_area_m2": 2 * (width * height + width * depth + height * depth),
        "child_center_m": [0.0, 0.0, depth / 2],
    }


def predict(neutral):
    request = neutral["part"]
    sketch, = request["document"]["sketches"]["$tuple"]
    feature, = request["document"]["feature_timeline"]["$tuple"]
    ends = [row["geometry"][point] for row in sketch["entities"]["$tuple"] for point in ("start", "end")]
    lo_x, hi_x = min(v["x"] for v in ends), max(v["x"] for v in ends)
    lo_y, hi_y = min(v["y"] for v in ends), max(v["y"] for v in ends)
    length = feature["definition"]["length"]
    curves.require(len(ends) == 8 and lo_x == -hi_x and lo_y == -hi_y and length["unit"] == "mm",
                   "expected the centered neutral four-edge front prism")
    part = request["settings"]["output"]["path_name"]
    sheet, = neutral["drawing_document"]["sheets"]["$tuple"]
    view, = sheet["views"]["$tuple"]
    link, = neutral["drawing_document"]["model_refs"]["$tuple"]
    curves.require(view["orientation_name"] == "*Front" and view["scale_ratio"]["$tuple"] == [1, 1]
                   and link["source_path"] == part, "expected a distinct neutral front-view reference")
    x, y = view["position"]["x"], view["position"]["y"]
    width, height, depth = (hi_x - lo_x) / 1000, (hi_y - lo_y) / 1000, length["value"] / 1000
    margin = min(sheet["width"], sheet["height"]) * 0.02
    a, b = sheet["scale_ratio"]["$tuple"]
    paper = [0, 13, a, b, 0, sheet["width"], sheet["height"], 1]
    def project(px, py):
        return {"sheet": sheet["name"], "sheet_properties": paper, "whats_wrong": 0,
                "view": {**geometry((width, height), px, py, depth), "name": view["name"],
                         "resolved_reference_path": part, "orientation": view["orientation_name"],
                         "configuration": view["configuration_name"],
                         "outline_m": [px - width / 2 - margin, py - height / 2 - margin,
                                       px + width / 2 + margin, py + height / 2 + margin]}}
    folder = neutral["native"]["options"]["folder_names"]
    support = neutral["support_names"]
    sheet_support = neutral["native"]["options"]["sheet_names"]
    title, view_name = sheet["name"], view["name"]
    drawings = [[folder[key], tag, None] for key, tag in (
        ("comments", "CommentsFolder"), ("blocks", "BlockFolder"), ("binder", "DocsFolder"),
        ("annotations", "DetailCabinet"), ("ink_markups", "InkMarkupFolder"), ("review_markups", "MarkupCommentFolder"),
    )]
    drawings.extend([[title, "DrSheet", None], [sheet_support["plane_name"], "RefPlane", title],
                     [sheet_support["profile_name"], "ProfileFeature", title], [sheet_support["detail_name"], "DetailFolder", title],
                     [view_name, "AbsoluteView", title], [support["detail"], "DetailFolder", view_name],
                     [support["sheet_plane"], "RefPlane", view_name], [support["sheet_profile"], "ProfileFeature", view_name],
                     [support["model_plane"], "RefPlane", view_name], [support["model_profile"], "ProfileFeature", view_name]])
    intent = {"profile": sketch["name"], "feature": feature["name"], "resolved_roots": 19}
    parts = [row[:2] for row in tree_prediction(request, {"intent": intent}) if row[2] is None]
    return {"first": project(x, y), "edited": project(x + 0.002731, y - 0.001739),
            "drawing_tree": drawings, "part_tree": parts, "child_parameters": {"D1@" + feature["name"]: depth}}


def verify(packet, expected_hash, guest):
    root = packet.parent
    job = read_json(checked(root, packet.name, expected_hash))
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
                   "expected locked disclosed drawing comparison")
    tools = root / "Tools"
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS),
                   "the frozen comparison requires its exact tool closure")
    for name, digest in job["tools_sha256"].items():
        checked(tools, name, digest)
    neutral = read_json(checked(root, "NeutralRequest.json", job["neutral_sha256"]))
    proofs = [read_json(checked(root, f"GuardedBuild{index}.json", job["each_guarded_build_sha256"])) for index in (1, 2)]
    proof = proofs[0]
    curves.require(proof == proofs[1] and proof["definition_round_trip"] and proof["actual_generated_child_identity"]
                   and proof["runtime_io_attempts"] == 0 and proof["face_downstream_count"] == 6
                   and proof["edge_downstream_count"] == 12 and not proof["native_acceptance"],
                   "the generated pair must have two guarded host proofs")
    control = read_json(checked(root, "Control.json", job["control_sha256"]))
    curves.require(control["drawing"]["sha256"] == CONTROL_DRAWING and control["part"]["sha256"] == CONTROL_PART,
                   "expected the locked pristine linked pair")
    controls = {key: checked(root, "Control/" + row["filename"], row["sha256"])
                for key, row in control.items() if key in STEMS}
    windows = {"drawing": PureWindowsPath(neutral["native"]["output"]["path_name"]),
               "part": PureWindowsPath(neutral["part"]["settings"]["output"]["path_name"])}
    curves.require(windows["drawing"].parent == windows["part"].parent and windows["drawing"].is_absolute()
                   and all(windows[key].name == name for key, name in STEMS.items())
                   and str(windows["part"]) == proof["model_reference"], "the encoded actual child differs")
    if guest:
        for key in STEMS:
            path = Path(windows[key])
            curves.require(path.is_file() and curves.digest(path) == proof[key + "_sha256"],
                           f"encoded {key} does not contain the exact generated bytes")
    return job, proof, control, controls, windows, predict(neutral)


def run(packet, expected_hash):
    curves.require(os.name == "nt", "use the Windows guest for native measurements")
    job, proof, control, controls, windows, prediction = verify(packet, expected_hash, True)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "Inspection"
    output.mkdir()
    result = {"schema": SCHEMA, "packet_sha256": expected_hash, "heldout_inputs_read": 0,
              "observed_cache_consumer": False, "phases": {}, "passed": False}
    stages = result["phases"]
    def checkpoint():
        curves.write_json(output / "Result.json", result)

    def measure(role, paths, hashes, initial, expected_edit, tree, observer):
        def perform(name, source, digest, expected, drawing_tree, edit):
            row = phase(Swapp, application_identity, directory=output / role / name, native=source, sha256=digest,
                        expected=expected, child=paths["part"], original_child=initial["view"]["resolved_reference_path"],
                        child_hash=hashes["part"], oracle=ORACLE, tree=drawing_tree, edit=edit,
                        expected_edit=expected_edit, observe=observer)
            stages[role + "/" + name] = row
            checkpoint()
            return row
        first = perform("OpenEditSave", paths["drawing"], hashes["drawing"], initial, tree, True)
        if not first["passed"]:
            return False
        second = perform("FreshReopen", output / role / "OpenEditSave/EditedDrawing.SLDDRW", first["derivative_sha256"],
                         expected_edit or first["edited"], first["tree"], False)
        return second["passed"]

    def control_run(role, tree=None):
        return measure(role, controls, {"drawing": CONTROL_DRAWING, "part": CONTROL_PART}, control["expected"], None, tree, None)

    before = generated = False
    try:
        before = control_run("ControlBefore")
        if before:
            paths = {key: Path(value) for key, value in windows.items()}
            hashes = {key: proof[key + "_sha256"] for key in windows}
            def observer(author, drawing, native):
                return observe_child(author, drawing, native, paths["part"], prediction["part_tree"], prediction)
            generated = measure("Generated", paths, hashes, prediction["first"], prediction["edited"],
                                prediction["drawing_tree"], observer)
    finally:
        after = control_run("ControlAfter", stages["ControlBefore/OpenEditSave"]["tree"] if before else None)
        unchanged = verify(packet, expected_hash, True)[0] == job
        starts = {row["oracle_identity"]["process_creation_filetime"] for row in stages.values() if "oracle_identity" in row}
        result.update(controls_healthy=before and after, generated_passed=generated, inputs_unchanged=unchanged,
                      distinct_processes=len(starts), exposed_generated_child_before_rebuild=
                      "initial_link" in stages.get("Generated/OpenEditSave", {}))
        result["passed"] = before and after and generated and unchanged and len(starts) == len(stages) == 6
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("verify-host", "verify-guest", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.action != "run":
        verify(packet, args.packet_sha256, args.action == "verify-guest")
        print('{"verified": true, "processes_started": 0}')
        return 0
    result = run(packet, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "generated_passed", "distinct_processes")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
