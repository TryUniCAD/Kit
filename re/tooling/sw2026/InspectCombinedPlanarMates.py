from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from shutil import copyfile
import time

from AuthorCurves import digest, require, write_json
from PlanarMateEdit import driving_request, predict_edit, verify_case


SCHEMA = "kit.sw2026.combined-planar-mate-discovery.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCRIPT = Path(__file__).resolve()
TOOLS = ("AssemblyMateEvidence.py", "AuthorAssemblySources.py", "AuthorCurves.py", "InspectCircleSketch.py",
         "InspectFresh.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "PlanarMateEdit.py", "Swapp.py", SCRIPT.name)
ROLES = ("ControlBefore", "Generated", "Reopen", "ControlAfter")


def check_file(root, row):
    path = (root / row["path"]).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file() and digest(path) == row["sha256"], "a frozen native input changed")
    return path


def verify(path, sha):
    root = path.parent.resolve(strict=True)
    require(digest(path) == sha, "use the frozen combined-mate packet")
    job = json.loads(path.read_bytes())
    attempt = job.get("attempt", "")
    require(not attempt or re.fullmatch(r"T[0-9]{2}", attempt), "invalid combined-mate attempt")
    tools = root / ("CompareTools" + attempt)
    require(SCRIPT.parent == tools, "use the exact observer tool directory")
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
            "the observer accepts the disclosed pinned plane-mate profile")
    require(set(job["tool_hashes"]) == set(TOOLS)
            and all(digest(tools / name) == job["tool_hashes"][name] for name in TOOLS), "an observer tool changed")
    require(set(job["inputs"]) == {"source_parent", "source_child", "generated_parent", "generated_child"},
            "unexpected paired input ownership")
    paths = {role: check_file(root, row) for role, row in job["inputs"].items()}
    freeze = root / ("GenerationFreeze" + attempt + ".json")
    require(digest(freeze) == job["generation_freeze_sha256"], "generated comparison custody changed")
    built = json.loads(freeze.read_bytes())
    require(re.fullmatch(r"[0-9a-f]{40}", job["writer_revision"]) and built["writer_revision"] == job["writer_revision"]
            and built["guarded_builds"] == 2 and built["runtime_file_reads"] == 0,
            "the generated comparison requires the exact guarded writer closure")
    require(all(built[role + "_sha256"] == job["inputs"]["generated_" + role]["sha256"]
                for role in ("parent", "child")), "generated parent and child were not frozen before comparison")
    require(all(paths[role + "_parent"].parent == paths[role + "_child"].parent for role in ("source", "generated")),
            "each parent needs its own local child")
    require(paths["source_parent"].name == paths["generated_parent"].name and
            paths["source_child"].name == paths["generated_child"].name and
            len(set(paths.values())) == 4, "source and generated lanes must use matching identities and separate paths")
    require(job["case"]["split"] == "discovery", "expected a disclosed group")
    verify_case(job["case"], job["fixed_occurrence"], job["edit_distance_m"])
    require(len(job["child_size_m"]) == 3 and all(math.isfinite(v) and v > 0 for v in job["child_size_m"]),
            "the part prediction requires its authored dimensions")
    return job, paths


def mass_prediction(job):
    width, height, depth = job["child_size_m"]
    return {"volume": width * height * depth, "area": 2 * (width * height + height * depth + width * depth),
            "com": (0.0, 0.0, depth / 2)}


def capture(author, model, assembly, child_path, case, mass, label):
    import Swapp
    from AssemblyMateEvidence import observe_plane_mates
    from AuthorAssemblySources import bound_child, feature_tree, placement_transform, snapshot

    expected = [placement_transform(item) for item in case["placements"]]
    observed = snapshot(author, model, assembly, expected, child_path, mass, label)
    observed["mates"] = observe_plane_mates(author, model, observed["occurrences"], case)
    require([value["name"] for value in observed["mates"]] == [value["name"] for value in case["mates"]],
            "the native mate group has a different authored order")
    child = bound_child(author, assembly, child_path, len(expected))
    observed["child_tree"] = feature_tree(author, child)
    observed["child_mass"] = Swapp.mass(child)
    require(int(author.get(author.get(child, "Extension"), "GetWhatsWrongCount")) == 0, "the part has native diagnostics")
    values = (observed["child_mass"]["volume"], observed["child_mass"]["area"], *observed["child_mass"]["com"])
    target = (mass["volume"], mass["area"], *mass["com"])
    require(all(math.isclose(a, b, rel_tol=5e-7, abs_tol=1e-12) for a, b in zip(values, target, strict=True)),
            "the measured child did not match the authored body")
    return observed


def native_save(author, model, assembly, parent, child, count, recorder):
    import Swapp
    from AuthorAssemblySources import save_owned_child

    owned = save_owned_child(author, assembly, child, count, recorder, parent.parent, basename=child.name)
    errors, warnings = Swapp.byref_long(), Swapp.byref_long()
    saved = recorder.call("persist generated parent after its child", Swapp.invoke, model, "Save3", Swapp.SAVE_SILENT, errors, warnings)
    status = [bool(saved), int(errors.value), int(warnings.value)]
    require(status == [True, 0, 0] and digest(child) == owned["native_sha256"], "native paired save failed or changed the child")
    return {"parent": digest(parent), "child": owned, "parent_status": status}


def phase(job, edit, role, parent, child, target, *, editing=False, reopened=None, observe=None,
          child_depth_edit=None, observe_edited=None):
    import Swapp
    from AssemblyMateEvidence import mate_features
    from AuthorAssemblySources import bound_child
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    target.mkdir()
    recorder = Recorder(target / "Record.json", {"role": role, "input": {"parent": digest(parent), "child": digest(child)}})
    result = {"role": role, "started_at": time.time(), "passed": False}
    controller = None
    case = edit if reopened else job["case"]
    count = len(case["placements"])
    mass = mass_prediction(job)
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle combined-mate oracle", Swapp.sweep)
            controller = recorder.call("start fresh combined-mate oracle", Swapp.Sw)
            identity = recorder.call("verify exact combined-mate oracle", application_identity, controller.app)
            require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2",
                    "unexpected oracle build")
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open exact paired native assembly", controller.open, parent, read_only=not editing)
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0 and Path(author.get(model, "GetPathName")).samefile(parent),
                    "native combined assembly failed, warned or resolved another path")
            assembly = author.typed(model, "AssemblyDoc")
            loaded_child = bound_child(author, assembly, child, count)
            result["child_stamp_on_open"] = int(author.get(loaded_child, "GetUpdateStamp"))
            result["initial"] = capture(author, model, assembly, child, case, mass, "initial")
            if observe is not None:
                result["initial_options"] = observe(author, model, loaded_child)
            require(author.get(model, "ForceRebuild3", False), "native assembly rebuild failed")
            result["rebuilt"] = capture(author, model, assembly, child, case, mass, "rebuilt")
            if observe is not None:
                result["rebuilt_options"] = observe(author, model, loaded_child)
            if editing and child_depth_edit is not None:
                name, depth = child_depth_edit
                require(name == "D1@Boss-Extrude1" and math.isfinite(depth) and 0 < depth != job["child_size_m"][2]
                        and edit == case and observe_edited is not None,
                        "child depth edit needs a changed blind length and the same ordered mates")
                parameter = author.get(loaded_child, "Parameter", name)
                require(parameter is not None and author.get(parameter, "DrivenState") == 2
                        and not author.get(parameter, "ReadOnly"), "the child has no actual editable blind depth")
                recorder.close_number("child blind depth before edit", author.get(parameter, "SystemValue"),
                                      job["child_size_m"][2])
                status = int(author.get(parameter, "SetSystemValue3", depth, 1, author.sw.nothing()))
                require(status == 0 and author.get(loaded_child, "ForceRebuild3", False)
                        and author.get(model, "ForceRebuild3", False), "the live child depth edit failed")
                result["edit_status"] = status
                updated = mass_prediction({**job, "child_size_m": [*job["child_size_m"][:2], depth]})
                result["edited"] = capture(author, model, assembly, child, case, updated, "edited child depth")
                result["edited_options"] = observe_edited(author, model, bound_child(author, assembly, child, count))
                require(result["edited"]["child_mass"]["volume"] != result["rebuilt"]["child_mass"]["volume"],
                        "the live child depth edit did not change the solid")
                result["saved"] = native_save(author, model, assembly, parent, child, count, recorder)
            elif editing:
                drive = driving_request(case)["name"]
                feature, = [value for value in mate_features(author, model) if author.get(value, "Name") == drive]
                display = author.get(feature, "GetFirstDisplayDimension")
                require(display is not None, "the native distance mate has no display")
                parameter = author.get(display, "GetDimension2", 0)
                status = int(author.get(parameter, "SetSystemValue3", job["edit_distance_m"], 1, author.sw.nothing()))
                require(status == 0 and author.get(model, "ForceRebuild3", False), "the live distance edit failed")
                result["edit_status"] = status
                result["edited"] = capture(author, model, assembly, child, edit, mass, "edited")
                if observe is not None:
                    result["edited_options"] = observe(author, model, loaded_child)
                require(result["edited"]["mass"]["com"] != result["rebuilt"]["mass"]["com"], "the distance edit did not move the solid")
                result["saved"] = native_save(author, model, assembly, parent, child, count, recorder)
            if reopened is not None:
                loaded_child = bound_child(author, assembly, child, count)
                result["child_stamp_after_rebuild"] = int(author.get(loaded_child, "GetUpdateStamp"))
                require(result["child_stamp_on_open"] == reopened["child"]["update_stamp"]
                        and digest(parent) == reopened["parent"] and digest(child) == reopened["child"]["native_sha256"],
                        "fresh combined open lost the synchronized child or saved parent")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress, finished_at=time.time())
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics")
                            and not recorder.data["cleanup_errors"] and recorder.data["first_failure"] is None)
    recorder.data.update(result=result, passed=result["passed"], finished_at=result["finished_at"])
    recorder.flush()
    result["record_sha256"] = digest(target / "Record.json")
    result["numeric_checks"] = len(recorder.data["checks"])
    return result


def signature(row):
    return {
        "tree": row["tree"], "child_tree": row["child_tree"],
        "occurrences": [{name: item[name] for name in ("placement_index", "name", "configuration", "fixed", "visible_child_bodies")}
                        for item in row["occurrences"]],
        "mates": [{name: item.get(name) for name in ("name", "type", "alignment", "dimension_name", "flipped")}
                  | {"endpoints": [endpoint["occurrence"] for endpoint in item["entities"]]} for item in row["mates"]],
    }


def run(packet, sha):
    require(os.name == "nt", "combined native observation requires the Windows guest")
    job, paths = verify(packet, sha)
    from AuthorAssemblySources import placement_transform
    edit = predict_edit(job["case"], job["edit_distance_m"], placement_transform)
    root = packet.parent
    attempt = job.get("attempt", "")
    output = root / ("Inspection" + attempt)
    output.mkdir()
    work = root / ("Working" + attempt)
    work.mkdir()
    parent = work / paths["generated_parent"].name
    child = work / paths["generated_child"].name
    for source, target in ((paths["generated_parent"], parent), (paths["generated_child"], child)):
        copyfile(source, target)
        require(digest(source) == digest(target), "untouched generated input differs")
    stages = []
    summary = {"schema": SCHEMA, "packet_sha256": sha, "phases": stages, "started_at": time.time(),
               "heldout_inputs_read": 0, "passed": False}

    def capture_phase(role, parent_value, child_value, **extra):
        row = phase(job, edit, role, parent_value, child_value, output / role, **extra)
        stages.append(row)
        write_json(output / "Result.json", summary)
        return row

    try:
        before = capture_phase("ControlBefore", paths["source_parent"], paths["source_child"])
        if before["passed"]:
            generated = capture_phase("Generated", parent, child, editing=True)
            if generated["passed"]:
                reopened = capture_phase("Reopen", parent, child, reopened=generated["saved"])
                a, b = signature(before["rebuilt"]), signature(generated["rebuilt"])
                summary["source_generated_checks"] = {key: a[key] == b[key] for key in a}
                summary["edit_identity_preserved"] = signature(generated["rebuilt"]) == signature(generated["edited"])
                summary["reopen_identity_preserved"] = bool(reopened["passed"] and signature(generated["edited"]) == signature(reopened["rebuilt"]))
    finally:
        after = capture_phase("ControlAfter", paths["source_parent"], paths["source_child"])
        summary["controls_healthy"] = bool(stages[0]["passed"] and after["passed"])
        summary["source_bracket_identity"] = bool(summary["controls_healthy"] and signature(stages[0]["rebuilt"]) == signature(after["rebuilt"]))
        summary["immutable_inputs_unchanged"] = all(digest(path) == job["inputs"][name]["sha256"] for name, path in paths.items())
        ids = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in stages}
        summary["distinct_processes"] = len({value for value in ids if type(value) is int and value > 0})
        summary["passed"] = bool([row["role"] for row in stages] == list(ROLES) and all(row["passed"] for row in stages)
                                 and summary["distinct_processes"] == 4 and summary["source_bracket_identity"]
                                 and summary["immutable_inputs_unchanged"] and all(summary.get("source_generated_checks", {"missing": False}).values())
                                 and summary.get("edit_identity_preserved") and summary.get("reopen_identity_preserved"))
        summary["finished_at"] = time.time()
        write_json(output / "Result.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.packet_sha256)
        result = {"passed": True, "native_processes_started": 0}
    else:
        summary = run(path, args.packet_sha256)
        result = {key: summary.get(key) for key in ("passed", "distinct_processes", "controls_healthy", "source_generated_checks")}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
