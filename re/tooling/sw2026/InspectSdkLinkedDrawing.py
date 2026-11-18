from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

import AuthorCurves as curves
from InspectFrontDrawingMap import TOOL_NAMES as DRAWING_TOOLS, phase
from InspectSdkBlindPart import ORACLE, tree_prediction


SCHEMA = "kit.sw2026.sdk-linked-drawing-native-trial.v1"
CONTROL_DRAWING = "2fd1d31f7f957def7fd2c73b3b88295aecb56c41d29dc208445b711c3d50c525"
CONTROL_PART = "4f752c0093f04a3a383b68bfaeaad8b0fc05285d064989d818c3dc92d990a1ce"
TOOLS = (*DRAWING_TOOLS, "AuthorRectangleAnchors.py", "InspectFresh.py", "InspectSdkBlindPart.py", Path(__file__).name)


def checked(root, entry, expected):
    path = (root / entry).resolve(strict=True)
    curves.require(path.is_relative_to(root) and path.is_file() and curves.digest(path) == expected,
                   f"the frozen linked drawing evidence changed: {entry}")
    return path


def verify(packet, sha):
    root = packet.parent.resolve(strict=True)
    job = json.loads(checked(root, packet.name, sha).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
                   "unexpected SDK linked drawing trial")
    tools = (root / "Tools").resolve(strict=True)
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS),
                   "the linked drawing trial must bind its complete observer")
    for name, expected in job["tools_sha256"].items():
        checked(tools, name, expected)
    fixture = json.loads(checked(root, "Fixture.json", job["fixture_sha256"]).read_bytes())
    neutral = json.loads(checked(root, "NeutralRequest.json", fixture["neutral_request_sha256"]).read_bytes())
    control = json.loads(checked(root, "Control.json", job["control_sha256"]).read_bytes())
    curves.require(fixture["heldout_inputs_read"] == 0 and fixture["guarded_builds"] == 2
                   and control["drawing"]["sha256"] == CONTROL_DRAWING and control["part"]["sha256"] == CONTROL_PART,
                   "the trial lacks its clean disclosed construction and pristine control")
    seed = {name: checked(root, "Control/" + control[name]["filename"], control[name]["sha256"]) for name in ("drawing", "part")}
    builds = [json.loads(checked(root, f"Build{index}.stdout", fixture["sdk_stdout_sha256"]).read_bytes()) for index in range(2)]
    reference = json.loads(checked(root, "Counterpart.stdout", fixture["counterpart_stdout_sha256"]).read_bytes())
    curves.require(builds[0] == builds[1] and builds[0]["passed"] and builds[0]["actual_generated_child_identity"]
                   and builds[0]["runtime_input_file_access_attempts"] == 0 and builds[0]["complete_sdk_only_linked_factory"]
                   and builds[0]["child_graph_reemission_unchanged"] and reference["passed"]
                   and reference["container_identical"] and reference["artifact_sha256"] == builds[0]["artifact_sha256"],
                   "two guarded SDK builds and an independent counterpart must bind the paired input")
    archived = fixture["files"]
    curves.require(len(archived) == 2 and set(map(lambda name: Path(name).suffix.upper(), archived)) == {".SLDDRW", ".SLDPRT"},
                   "a genuine linked drawer must contain one drawing and one part")
    paths = {}
    target_root = PureWindowsPath(fixture["windows_root"])
    for name, row in archived.items():
        target = PureWindowsPath(row["encoded_windows_path"])
        curves.require(target.is_absolute() and target.is_relative_to(target_root) and target.name == name,
                       "guest paths must preserve the authored linked document identities")
        source = checked(root, "Generated/" + name, row["sha256"])
        key = "drawing" if target.suffix.upper() == ".SLDDRW" else "part"
        artifact = "artifact_sha256" if key == "drawing" else "child_artifact_sha256"
        curves.require(source.stat().st_size == row["bytes"] and builds[0][artifact] == row["sha256"],
                       "guarded SDK output differs from the planned guest artifact")
        paths[key] = (source, target, row["sha256"])
    curves.require(paths["drawing"][1].parent == paths["part"][1].parent and len(fixture["drawing_tree"]) == 16,
                   "incomplete linked drawing feature tree or paired directory")
    return job, fixture, neutral, control, seed, paths


def observe_child(author, drawing, native, wanted, part_tree, fixture):
    curves.require(Path(author.get(author.model, "GetPathName")).samefile(native), "opened a different native drawing")
    sentinel = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sentinel, "GetNextView"), "View")
    child = author.get(view, "ReferencedDocument")
    curves.require(Path(author.get(child, "GetPathName")).samefile(wanted), "view lost the exact generated child")
    rows = author.rec.call("read linked child top-level history", author.sw.features, child)
    curves.require([[row["name"], row["type"]] for row in rows] == part_tree and
                   all(row.get("error") == 0 and row.get("warning") is False and row.get("suppressed") is False for row in rows),
                   "linked child history differs from the modeled native names or feature classes")
    for name, expected in fixture["child_parameters"].items():
        parameter = author.get(child, "Parameter", name)
        curves.require(author.get(parameter, "DrivenState") == 2 and not author.get(parameter, "ReadOnly"),
                       "linked child lost an editable depth")
        author.rec.close_number(name, author.get(parameter, "SystemValue"), expected)
    sketch, boss = part_tree[-2][0], part_tree[-1][0]
    support = part_tree[-6][0]
    parents = {}
    for name in (sketch, boss):
        feature = author.get(child, "FeatureByName", name)
        parents[name] = [str(author.get(item, "Name")) for item in author.get(feature, "GetParents") or ()]
    curves.require(parents == {sketch: [support], boss: [sketch, support]}, "linked child lost its profile and From owners")
    return {"parents": parents, "tree": rows, "editable_depths": list(fixture["child_parameters"])}


def run(packet, packet_sha):
    curves.require(os.name == "nt", "the native linked trial requires the Windows guest")
    job, fixture, neutral, control, seed, paths = verify(packet, packet_sha)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "Inspection"
    output.mkdir()
    result = {"schema": SCHEMA, "packet_sha256": packet_sha, "phases": {}, "passed": False, "heldout_inputs_read": 0}
    stages = result["phases"]

    def checkpoint():
        curves.write_json(output / "Result.json", result)

    projected = fixture["child_history_sequence"]
    intent = {"resolved_roots": len(projected), "profile": projected[-2][0], "feature": projected[-1][0]}
    part_tree = [row[:2] for row in tree_prediction(neutral["part"], {"intent": intent}) if row[2] is None]

    def measure(role, drawing, child, expected, hashes, tree=None, *, inspect=False):
        native_path, part_path = drawing, child
        drawing_sha, part_sha = hashes
        observer = None
        if inspect:
            def observer(author, live_drawing, native):
                return observe_child(author, live_drawing, native, part_path, part_tree, fixture)

        first = phase(Swapp, application_identity, directory=output / role / "OpenEditSave", native=native_path, sha256=drawing_sha,
                      expected=expected, child=part_path, original_child=expected["view"]["resolved_reference_path"],
                      child_hash=part_sha, oracle=ORACLE, tree=tree, edit=True, observe=observer,
                      expected_edit=fixture["expected_after"] if inspect else None)
        stages[role + "/OpenEditSave"] = first
        checkpoint()
        if not first["passed"]:
            return first, False
        second = phase(Swapp, application_identity, directory=output / role / "FreshReopen",
                       native=output / role / "OpenEditSave" / "EditedDrawing.SLDDRW", sha256=first["derivative_sha256"],
                       expected=fixture["expected_after"] if inspect else first["edited"], child=part_path,
                       original_child=expected["view"]["resolved_reference_path"],
                       child_hash=part_sha, oracle=ORACLE, tree=first["tree"], edit=False, observe=observer)
        stages[role + "/FreshReopen"] = second
        checkpoint()
        return first, second["passed"]

    def control_lane(role, tree=None):
        return measure(role, seed["drawing"], seed["part"], control["expected"], (CONTROL_DRAWING, CONTROL_PART), tree)

    before = None
    healthy_before = candidate_pass = False
    try:
        before, healthy_before = control_lane("ControlBefore")
        if healthy_before:
            for source, raw_target, expected in paths.values():
                target = Path(raw_target)
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open("rb") as input_file, target.open("xb") as output_file:
                    copyfileobj(input_file, output_file)
                curves.require(curves.digest(target) == expected, "staged linked SDK bytes changed")
            _, candidate_pass = measure("Generated", Path(paths["drawing"][1]), Path(paths["part"][1]),
                                        fixture["expected_before"], (paths["drawing"][2], paths["part"][2]),
                                        fixture["drawing_tree"], inspect=True)
    except Exception as error:
        result["error"] = repr(error)
    finally:
        _, healthy_after = control_lane("ControlAfter", before["tree"] if healthy_before else None)
        terminal, _, _, _, _, _ = verify(packet, packet_sha)
        unchanged = terminal == job and all(Path(target).is_file() and curves.digest(Path(target)) == expected
                                            for _, target, expected in paths.values())
        starts = {row["oracle_identity"]["process_creation_filetime"] for row in stages.values() if row.get("oracle_identity")}
        result.update(controls_healthy=healthy_before and healthy_after, generated_passed=candidate_pass,
                      inputs_unchanged=unchanged, distinct_processes=len(starts))
        result["passed"] = result["controls_healthy"] and candidate_pass and unchanged and len(starts) == len(stages) == 6
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser(description="Measure a complete SDK linked drawing and its generated part")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        print('{"passed": true, "processes_started": 0}')
        return 0
    result = run(packet, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "generated_passed", "distinct_processes")}, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
