from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from InspectRectangleDimensions import centers_match, close


CASES = ("A13SyncedSingle", "A14SyncedRepeat")
EDITS = (("Width", "D1@Sketch1"), ("Height", "D2@Sketch1"), ("Depth", "D1@Boss-Extrude1"))
TOOL_FILES = (
    "AuthorAssemblySources.py", "AuthorCurves.py", "InspectCircleSketch.py",
    "InspectFresh.py", "InspectRectangleDimensions.py", "ObserveAssemblyLoad.py",
    "OracleIdentity.py", "ProbeAssemblyRebuild.py", "Swapp.py",
)


def verified(path, expected, *, stage):
    path = path.resolve(strict=True)
    require(path.is_file() and path.is_relative_to(stage), "an input escaped the staged discovery directory")
    require(digest(path) == expected, f"staged input digest differs for {path.name}")
    return path


def files_for(*, stage, folder, entries, case):
    names = (case + ".SLDASM", "CohortChild.SLDPRT")
    require(set(entries) == set(names), "unexpected assembly or child file names")
    return {name: verified(stage / folder / name, entries[name], stage=stage) for name in names}


def inputs(job, job_path):
    require(job["schema"] == "kit.sw2026.dimensioned-assembly-discovery-job.v1", "unexpected assembly discovery job schema")
    checkout = Path(job["checkout_root"]).resolve(strict=True)
    stage = Path(job["stage"]).resolve(strict=True)
    output = Path(job["output"]).resolve()
    require(not stage.is_relative_to(checkout) and job_path.parent == stage and output == stage / "Inspection", "assembly discovery needs external exact staging and output paths")
    source_snapshot = verified(stage / "SourceSnapshot.json", job["source_snapshot_sha256"], stage=stage)
    source = json.loads(source_snapshot.read_bytes())
    require(tuple(case["name"] for case in job["cases"]) == CASES and tuple(source["cases"]) == CASES, "disclosed discovery case membership differs")
    require(set(job["dimensions"]) == {name for _, name in EDITS}, "baseline dimension set differs")
    result = {}
    for case in job["cases"]:
        name = case["name"]
        reference = source["cases"][name]
        native = files_for(stage=stage, folder=Path("NativeSources") / name, entries=reference["files"], case=name)
        require(tuple((row["title"], row["parameter"]) for row in case["trials"]) == EDITS, "discovery needs separate width, height and depth edits")
        for trial in case["trials"]:
            parameter = trial["parameter"]
            value = trial["value_m"]
            require(value != job["dimensions"][parameter] and trial["dimensions"] == job["dimensions"] | {parameter: value}, "trial must change only its requested driving parameter")
        result[name] = {
            "reference": reference,
            "native": native,
            "generated": {
                trial["title"]: files_for(
                    stage=stage, folder=Path("Generated") / name / trial["title"], entries=trial["files"], case=name,
                )
                for trial in case["trials"]
            },
        }
    control = verified(stage / job["control"]["file"], job["control"]["sha256"], stage=stage)
    return output, control, result


def require_dimensions(actual, expected):
    require(set(actual) == set(expected), "native dimension lookup did not cover its requested names")
    require(all(close(actual[name], value, relative=0, absolute=1e-12) for name, value in expected.items()), f"native dimensions differ from their targets: {actual!r}")


def configurations(author, model):
    names = list(author.get(model, "GetConfigurationNames") or ())
    manager = author.get(model, "ConfigurationManager")
    active = str(author.get(author.get(manager, "ActiveConfiguration"), "Name"))
    return {"names": names, "active": active}


def projected_tree(rows):
    return [{name: row[name] for name in ("name", "type", "parent")} for row in rows]


def scene(author, parent, assembly, child, child_path, trial, expected, dimensions, root_tree, phase):
    import Swapp
    from AuthorAssemblySources import feature_tree, snapshot
    from ProbeAssemblyRebuild import model_state

    child_metrics = author.rec.call("measure resolved child in system units", Swapp.mass, child)
    require(child_metrics is not None and "error" not in child_metrics, "resolved child has no mass properties")
    child_bodies = author.rec.call("count solid bodies of resolved child", Swapp.bodies, child)
    require(child_bodies == 1 and all(close(child_metrics.get(key), expected[key]) for key in ("volume", "area", "mass")), f"child body or mass properties differ: {child_metrics!r}")
    center = child_metrics.get("com")
    require(isinstance(center, list) and len(center) == 3, "child centroid is missing")
    require(all(type(value) in (float, int) and math.isfinite(value) and (target is None or close(value, target))
                for value, target in zip(center, expected["center"], strict=True)), f"child centroid differs: {center!r}")
    child_parameters = author.rec.call("read all driving child parameters", Swapp.parameters, child, tuple(dimensions))
    require_dimensions(child_parameters, dimensions)
    parent_config, child_config = (configurations(author, doc) for doc in (parent, child))
    require(parent_config == child_config == {"names": ["Default"], "active": "Default"}, "assembly or child configuration differs")
    dimensions_owned = model_state(author, child)
    require(dimensions_owned["whats_wrong"] == 0, "rebuild warnings or errors in the resolved child")
    root = snapshot(author, parent, assembly, trial["expected_placement"], child_path, expected | {"com": center}, phase)
    assembly_mass = root["mass"].get("mass")
    require(type(assembly_mass) in (int, float) and math.isfinite(assembly_mass) and assembly_mass > 0, "assembly mass is invalid")
    require([item["name"] for item in root["occurrences"]] == trial["names"], "assembly occurrence naming differs")
    require(all(item["configuration"] == "Default" and not item["fixed"] for item in root["occurrences"]), "assembly occurrence is fixed or selects a different child configuration")
    return {
        "assembly": root | {"configuration": parent_config, "source_tree_matches": projected_tree(root["tree"]) == root_tree},
        "child": {
            "configuration": child_config, "tree": feature_tree(author, child), "parameters": child_parameters,
            "mass": child_metrics, "body_count": child_bodies, "state": dimensions_owned,
        },
    }


def measured_phase(*, job, entry, trial, lane, folder, reference, parent_path, child_path, expected, save, preload):
    import Swapp
    from AuthorAssemblySources import bound_child, save_owned_child
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ProbeAssemblyRebuild import model_state

    report_path = folder / ("EditRun.json" if save else "SavedReopen.json")
    recorder = Recorder(report_path, {"case": entry["name"], "trial": trial["title"], "lane": lane, "save": save})
    input_digests = {str(path): digest(path) for path in (parent_path, child_path)}
    result = {"opened": False, "source_preload": preload, "input_sha256": input_digests, "passed": False}
    controller = parent = None
    root_tree = reference["native_root_tree"]["ordered_nodes"]
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify isolated oracle is idle", Swapp.sweep)
            controller = recorder.call("launch fresh oracle process", Swapp.Sw)
            identity = recorder.call("verify pinned SOLIDWORKS executable", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "unexpected SOLIDWORKS executable")
            author = CurveAuthor(controller.app, recorder, Swapp)
            if preload:
                loaded, errors, warnings = recorder.call("open the source comparison child copy at its relocated path", controller.open, child_path)
                require(loaded is not None and errors == warnings == 0, "source child copy failed or warned on open")
            parent, errors, warnings = recorder.call("open the native assembly", controller.open, parent_path, read_only=not save)
            result.update(opened=parent is not None, open_errors=errors, open_warnings=warnings)
            require(parent is not None and errors == warnings == 0, "assembly failed or warned on open")
            assembly = author.typed(parent, "AssemblyDoc")
            count = len(trial["names"])
            child = recorder.call("resolve the exact staged child across all occurrences", bound_child, author, assembly, child_path, count)
            result["after_open"] = {
                "component_count": int(author.get(assembly, "GetComponentCount", True)),
                "child_body_count": Swapp.bodies(child),
                "parent": model_state(author, parent),
                "child": model_state(author, child),
                "child_stamp": int(author.get(child, "GetUpdateStamp")),
            }
            if not save:
                require(input_digests == expected["files"] and result["after_open"]["child_stamp"] == expected["child_stamp"], "fresh reopen did not resolve the synchronized save state")
            require(bool(recorder.call("force initial parent rebuild", author.get, parent, "ForceRebuild3", False)), "parent rebuild failed")
            result["rebuilt"] = recorder.call(
                "measure rebuilt assembly and its child", scene, author, parent, assembly, child, child_path, trial,
                job["geometry"] if save else trial["geometry"], job["dimensions"] if save else trial["dimensions"], root_tree, "rebuilt",
            )
            if save:
                parameter = author.get(child, "Parameter", trial["parameter"])
                require(parameter is not None, "requested driving child parameter is unavailable")
                author.set(parameter, "SystemValue", trial["value_m"])
                require(bool(recorder.call("force edited child rebuild", author.get, child, "ForceRebuild3", False)), "edited child rebuild failed")
                require(bool(recorder.call("force edited parent rebuild", author.get, parent, "ForceRebuild3", False)), "edited parent rebuild failed")
                result["edited"] = recorder.call(
                    "measure the edited synchronized pair", scene, author, parent, assembly, child, child_path, trial,
                    trial["geometry"], trial["dimensions"], root_tree, "edited",
                )
                child_save = save_owned_child(author, assembly, child_path, count, recorder, folder)
                derivative = folder / "Edited.SLDASM"
                parent_save = recorder.call("save the parent after the edited child", controller.save_as, parent, derivative)
                require(list(parent_save) == [True, 0, 0] and derivative.is_file(), "edited parent save failed or warned")
                require(digest(child_path) == child_save["native_sha256"] and int(author.get(child, "GetUpdateStamp")) == child_save["update_stamp"], "parent save modified the synchronized child")
                result["save"] = {
                    "parent": str(derivative), "parent_status": list(parent_save), "child": child_save,
                    "files": {str(path): digest(path) for path in (derivative, child_path)}, "child_stamp": child_save["update_stamp"],
                }
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if parent is not None:
                        recorder.call("close the owned assembly", controller.close_doc, parent)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = monitor.log
    result["parent_input_unchanged"] = digest(parent_path) == input_digests[str(parent_path)]
    result["child_digest_matches"] = digest(child_path) == (result["save"]["child"]["native_sha256"] if "save" in result else input_digests[str(child_path)])
    result["passed"] = bool(result["passed"] and result["parent_input_unchanged"] and result["child_digest_matches"]
                            and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, finished_at=time.time())
    recorder.flush()
    return result


def clone_lane(files, hashes, folder, case):
    folder.mkdir(parents=True, exist_ok=False)
    for name, source in files.items():
        require(digest(source) == hashes[name], "immutable trial input changed before copying")
        target = folder / name
        copyfile(source, target)
        require(digest(target) == hashes[name], "trial copy differs from its frozen input")
    return folder / (case + ".SLDASM"), folder / "CohortChild.SLDPRT"


def occurrence_signature(scene):
    return [tuple(item[key] for key in ("name", "configuration", "fixed", "visible_child_bodies")) for item in scene["assembly"]["occurrences"]]


def compare_scenes(observed, expected):
    from AuthorAssemblySources import transform_matches

    return {
        "root_tree": (observed["assembly"]["source_tree_matches"] and expected["assembly"]["source_tree_matches"]
                      and observed["assembly"]["tree"] == expected["assembly"]["tree"]),
        "child_tree": observed["child"]["tree"] == expected["child"]["tree"],
        "occurrences": occurrence_signature(observed) == occurrence_signature(expected),
        "transform": all(transform_matches(new["transform"], old["transform"]) for new, old in zip(
            observed["assembly"]["occurrences"], expected["assembly"]["occurrences"], strict=True,
        )),
        "configuration": all(observed[kind]["configuration"] == expected[kind]["configuration"] for kind in ("assembly", "child")),
        "mass_properties": all(
            all(close(observed[kind]["mass"][key], expected[kind]["mass"][key]) for key in ("volume", "area", "mass"))
            and centers_match(observed[kind]["mass"]["com"], expected[kind]["mass"]["com"]) for kind in ("assembly", "child")
        ),
        "dimension_values": all(close(value, expected["child"]["parameters"][name], relative=0, absolute=1e-12)
                                for name, value in observed["child"]["parameters"].items()),
    }


def compare_trial(job, case, trial, case_inputs, work, evidence, phases, checkpoint):
    evidence["lanes"] = {}
    reference = case_inputs["reference"]
    for lane, files, hashes in (
        ("Source", case_inputs["native"], reference["files"]),
        ("Generated", case_inputs["generated"][trial["title"]], trial["files"]),
    ):
        folder = work / case["name"] / trial["title"] / lane
        parent, child = clone_lane(files, hashes, folder, case["name"])
        row = {}
        evidence["lanes"][lane] = row
        before = measured_phase(job=job, entry=case, trial=trial, lane=lane, folder=folder, reference=reference,
                                parent_path=parent, child_path=child, expected=None, save=True, preload=lane == "Source")
        phases.append(before)
        row["edit"] = before
        checkpoint()
        if "save" in before:
            saved = before["save"]
            reopen = measured_phase(job=job, entry=case, trial=trial, lane=lane, folder=folder, reference=reference,
                                    parent_path=Path(saved["parent"]), child_path=child, expected=saved, save=False, preload=False)
            phases.append(reopen)
            row["reopen"] = reopen
            checkpoint()
    source, generated = (evidence["lanes"][lane] for lane in ("Source", "Generated"))
    evidence["native_phases_passed"] = all(row.get(kind, {}).get("passed", False) for row in (source, generated) for kind in ("edit", "reopen"))
    evidence["comparisons"] = {}
    if evidence["native_phases_passed"]:
        evidence["comparisons"].update(
            baseline=compare_scenes(generated["edit"]["rebuilt"], source["edit"]["rebuilt"]),
            edited=compare_scenes(generated["edit"]["edited"], source["edit"]["edited"]),
            reopened=compare_scenes(generated["reopen"]["rebuilt"], source["reopen"]["rebuilt"]),
            source_save=compare_scenes(source["reopen"]["rebuilt"], source["edit"]["edited"]),
            generated_save=compare_scenes(generated["reopen"]["rebuilt"], generated["edit"]["edited"]),
        )
    evidence["passed"] = bool(evidence["native_phases_passed"] and all(all(comparison.values()) for comparison in evidence["comparisons"].values()))
    checkpoint()


def main():
    from InspectFresh import healthy, inspect

    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    output, control, data = inputs(job, job_path)
    output.mkdir(exist_ok=False)
    immutable = {control: job["control"]["sha256"]}
    for case in job["cases"]:
        bound = data[case["name"]]
        immutable.update((path, bound["reference"]["files"][key]) for key, path in bound["native"].items())
        for trial in case["trials"]:
            immutable.update((path, trial["files"][key]) for key, path in bound["generated"][trial["title"]].items())
    report = {
        "schema": "kit.sw2026.dimensioned-assembly-discovery.v1",
        "job_sha256": digest(job_path), "source_snapshot_sha256": job["source_snapshot_sha256"],
        "generator": job["generator"], "oracle_sha256": job["oracle_sha256"], "started_at": time.time(),
        "tool_sha256": {name: digest(Path(__file__).with_name(name)) for name in (*TOOL_FILES, Path(__file__).name)},
        "cases": [], "controls": [], "passed": False, "heldout_acceptance": False,
    }
    phases = []

    def checkpoint():
        write_json(output / "Inspection.json", report)

    def control_phase(label):
        row = {"kind": label}
        phases.append(row)
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row.get("sha256") == job["control"]["sha256"]
                              and row.get("oracle_identity", {}).get("sha256") == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    try:
        if control_phase("before"):
            for case in job["cases"]:
                case_rows = {"name": case["name"], "trials": []}
                report["cases"].append(case_rows)
                for trial in case["trials"]:
                    evidence = {"title": trial["title"], "parameter": trial["parameter"], "value_m": trial["value_m"]}
                    case_rows["trials"].append(evidence)
                    compare_trial(job, case, trial, data[case["name"]], output / "Work", evidence, phases, checkpoint)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            control_phase("after")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        report["input_files_unchanged"] = all(path.is_file() and digest(path) == value for path, value in immutable.items())
        report["controls_healthy"] = [row.get("healthy") for row in report["controls"]] == [True, True]
        identities = [row.get("oracle_identity", {}).get("process_creation_filetime") for row in phases]
        report["distinct_processes"] = len({value for value in identities if type(value) is int and value > 0})
        report["expected_processes"] = 2 + 4 * len(EDITS) * len(CASES)
        expected_trials = len(EDITS) * len(CASES)
        trials = [row for case in report["cases"] for row in case["trials"]]
        report["passed"] = bool(
            report["controls_healthy"] and report["input_files_unchanged"] and "exception" not in report
            and len(identities) == report["distinct_processes"] == report["expected_processes"]
            and len(trials) == expected_trials and all(row.get("passed") for row in trials)
        )
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": report["passed"], "controls_healthy": report["controls_healthy"], "cases": len(report["cases"])}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
