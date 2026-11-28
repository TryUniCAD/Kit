from __future__ import annotations

import argparse
import json
import math
import time
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from NestedAssemblySourcePlan import (
    CONTROL_SHA, HEIGHT, ORACLE, PARAMETERS, WIDTH, cases_from, expected_tree, load_deck, matches_transform, part_geometry,
)


def exact_file(value, path):
    actual = Path(str(value))
    return actual.is_file() and actual.samefile(path)


def file_paths(directory, case):
    return {row["name"]: directory / (row["name"] + suffix)
            for section, suffix in (("parts", ".SLDPRT"), ("assemblies", ".SLDASM")) for row in case[section]}


def active_configuration(author, model):
    manager = author.get(model, "ConfigurationManager")
    active = author.get(manager, "ActiveConfiguration")
    require(list(author.get(model, "GetConfigurationNames") or ()) == ["Default"] and author.get(active, "Name") == "Default",
            "nested source requires its single Default configuration")
    return active


def match_geometry(actual, expected):
    require(isinstance(actual, dict) and "error" not in actual and actual.get("mass", 0) > 0, "native document has no valid mass properties")
    values = [actual.get("volume"), actual.get("area"), *actual.get("com", ())]
    targets = [expected["volume"], expected["area"], *expected["com"]]
    require(len(values) == len(targets) and all(isinstance(x, (float, int)) and math.isclose(x, y, rel_tol=5e-7, abs_tol=1e-12)
                                                for x, y in zip(values, targets, strict=True)),
            f"native mass properties differ from the independent model: {actual!r}")


def measure_document(author, model, path, expected, depth=None):
    import Swapp
    from AuthorAssemblySources import feature_tree

    require(exact_file(author.get(model, "GetPathName"), path), "native definition resolves outside its owned source file")
    active_configuration(author, model)
    extension = author.get(model, "Extension")
    problems = int(author.get(extension, "GetWhatsWrongCount"))
    require(problems == 0, "native source definition has rebuild warnings or errors")
    stamp = int(author.get(model, "GetUpdateStamp"))
    mass = author.rec.call("measure native document mass and centroid", Swapp.mass, model)
    match_geometry(mass, expected)
    result = {"sha256": digest(path), "name": path.name, "tree": feature_tree(author, model), "mass_properties": mass,
              "update_stamp": stamp, "whats_wrong": problems,
              "needs_rebuild": int(author.get(extension, "NeedsRebuild2"))}
    if depth is not None:
        values = author.rec.call("read independent prism driving dimensions", Swapp.parameters, model, PARAMETERS)
        require(all(isinstance(values.get(key), (float, int)) and math.isclose(values[key], wanted, rel_tol=0.0, abs_tol=1e-12)
                    for key, wanted in zip(PARAMETERS, (WIDTH, HEIGHT, depth), strict=True)), "native leaf driving dimensions differ")
        require(Swapp.bodies(model) == 1, "native leaf has an unexpected solid body count")
        result["dimensions_m"] = values
    return result


def measure_occurrences(author, native, predicted, paths, definitions):
    children = author.get(native, "GetChildren") or ()
    require(len(children) == len(predicted), "native immediate child count differs from the authored hierarchy")
    measured = {}
    used = set()
    for value in children:
        component = author.typed(value, "Component2")
        pathname = author.get(component, "GetPathName")
        transform = author.typed(author.get(component, "Transform2"), "MathTransform")
        matrix = [float(item) for item in author.get(transform, "ArrayData")]
        candidates = [row for row in predicted if row["ordinal"] not in used and exact_file(pathname, paths[row["target"]]) and
                      matches_transform(matrix, row["world"])]
        require(len(candidates) == 1, f"native child did not match a unique authored world placement: {matrix!r}")
        expected, = candidates
        ordinal, target = expected["ordinal"], expected["target"]
        used.add(ordinal)
        model = author.get(component, "GetModelDoc2")
        require(model is not None and exact_file(author.get(model, "GetPathName"), paths[target]), "component resolved to a different physical model")
        require(author.get(component, "ReferencedConfiguration") == "Default" and not author.get(component, "IsSuppressed") and
                not author.get(component, "IsHidden", False), "nested source component is hidden, suppressed or configured differently")
        definitions.setdefault(target, model)
        row = {"name": str(author.get(component, "Name2")), "target": target, "world": matrix, "authored_local": expected["local"],
               "fixed": bool(author.get(component, "IsFixed")), "configuration": "Default", "kind": expected["kind"]}
        if expected["kind"] == "part":
            part = author.typed(model, "PartDoc")
            row["body_count"] = len(author.get(part, "GetBodies2", 0, True) or ())
            require(row["body_count"] == 1 and not (author.get(component, "GetChildren") or ()), "part occurrence must supply one visible body and no children")
            row["children"] = []
        else:
            author.typed(model, "AssemblyDoc")
            row["children"] = measure_occurrences(author, component, expected["children"], paths, definitions)
            row["body_count"] = sum(child["body_count"] for child in row["children"])
        measured[ordinal] = row
    require(len({item["name"] for item in measured.values()}) == len(children), "native siblings did not retain distinct occurrence names")
    return [measured[index] for index in range(len(predicted))]


def measure_tree(author, model, case, paths, *, owner=None, edited=False):
    expected = expected_tree(case, owner=owner, edited=edited)
    active = active_configuration(author, model)
    assembly = author.typed(model, "AssemblyDoc")
    root = author.get(active, "GetRootComponent3", True)
    require(root is not None, "native assembly configuration has no root component")
    root = author.typed(root, "Component2")
    name = expected["owner"]
    definitions = {name: model}
    children = measure_occurrences(author, root, expected["children"], paths, definitions)
    top = int(author.get(assembly, "GetComponentCount", True))
    total = int(author.get(assembly, "GetComponentCount", False))
    count = sum(row["body_count"] for row in children)
    require(top == len(children) and total == expected["total_occurrences"] and count == expected["body_count"], "native expanded counts differ")
    metrics = {"root": name, "occurrences": children, "top_level_count": top, "total_occurrences": total, "body_count": count,
               "expected_geometry": {key: expected[key] for key in ("body_count", "volume", "area", "com")}, "definitions": {}}
    depths = {row["name"]: row["depth_m"] for row in case["parts"]}
    if edited:
        depths[case["edit"]["part"]] = case["edit"]["depth_m"]
    for target, document in definitions.items():
        depth = depths.get(target)
        geometry = part_geometry(depth) if depth is not None else expected_tree(case, owner=target, edited=edited)
        metrics["definitions"][target] = measure_document(author, document, paths[target], geometry, depth)
    return metrics, definitions


def save_current(author, model, path, directory):
    import Swapp

    require(path.resolve().is_relative_to(directory.resolve()) and exact_file(author.get(model, "GetPathName"), path),
            "native save may only change an exact owned source sibling")
    before_stamp = int(author.get(model, "GetUpdateStamp"))
    author.get(model, "SetSaveFlag")
    require(bool(author.get(model, "GetSaveFlag")), "owned native source did not become dirty")
    errors, warnings = Swapp.byref_long(), Swapp.byref_long()
    passed = author.rec.call("save owned dependency before its owners", Swapp.invoke, model, "Save3", Swapp.SAVE_SILENT, errors, warnings)
    status = [bool(passed), int(errors.value), int(warnings.value)]
    after_stamp = int(author.get(model, "GetUpdateStamp"))
    require(status == [True, 0, 0] and path.is_file() and after_stamp == before_stamp, "synchronized native source save failed, warned or advanced the stamp")
    return {"status": status, "update_stamp": after_stamp, "sha256": digest(path), "bytes": path.stat().st_size}


def force_rebuild(author, model):
    require(bool(author.get(model, "ForceRebuild3", False)), "native source rebuild failed")


def edit_depth(author, model, value):
    dimension = author.get(model, "Parameter", PARAMETERS[2])
    require(dimension is not None, "native part has no driving extrude depth")
    author.set(dimension, "SystemValue", value)


def author_parts(author, controller, case, paths, seed, directory):
    models = {}
    for part in case["parts"]:
        name, depth = part["name"], part["depth_m"]
        path = paths[name]
        copyfile(seed, path)
        require(digest(path) == CONTROL_SHA, "owned rectangular seed differs from the pinned native control")
        model, errors, warnings = author.rec.call("open exact owned rectangular seed", controller.open, path)
        require(model is not None and errors == warnings == 0 and exact_file(author.get(model, "GetPathName"), path), "leaf seed failed native open")
        edit_depth(author, model, depth)
        force_rebuild(author, model)
        measure_document(author, model, path, part_geometry(depth), depth)
        save_current(author, model, path, directory)
        models[name] = model
    return models


def author_assemblies(author, controller, case, paths, models, result):
    import Swapp
    from AuthorAssemblySources import placement_transform

    template = Path(author.rec.call("read default assembly template", controller.template, "assembly"))
    require(template.is_absolute() and template.is_file() and template.suffix.casefold() == ".asmdot", "registered assembly template is unavailable")
    result["assembly_template_sha256"] = digest(template)
    result["authoring_definitions"] = {}
    for assembly in case["assemblies"]:
        name = assembly["name"]
        model = author.get(controller.app, "NewDocument", str(template), 0, 0, 0)
        require(model is not None, "native empty assembly creation failed")
        api = author.typed(model, "AssemblyDoc")
        entries = assembly["occurrences"]
        files = [str(paths[entry["target"]]) for entry in entries]
        matrices = [value for entry in entries for value in placement_transform(entry["placement"])]
        coordinate_names = [""] * len(entries)
        arrays = [Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | dtype, data) for dtype, data in
                  ((Swapp.pythoncom.VT_BSTR, files), (Swapp.pythoncom.VT_R8, matrices), (Swapp.pythoncom.VT_BSTR, coordinate_names))]
        components = author.rec.call("insert ordinary resolved child documents", api.AddComponents3, *arrays,
                                     parameters={"files": files, "transforms": matrices, "coordinate_system_names": coordinate_names})
        require(components is not None and len(components) == len(entries), "native insertion returned the wrong component count")
        force_rebuild(author, model)
        status = author.rec.call("first save of owned assembly definition", controller.save_as, model, paths[name])
        require(list(status) == [True, 0, 0] and paths[name].is_file(), "native first assembly save failed or warned")
        metrics, _ = measure_tree(author, model, case, paths, owner=name)
        result["authoring_definitions"][name] = metrics
        models[name] = model


def author_case(author, controller, case, paths, seed, directory, result):
    models = author_parts(author, controller, case, paths, seed, directory)
    author_assemblies(author, controller, case, paths, models, result)
    name = case["assemblies"][-1]["name"]
    root = models[name]
    edit = case["edit"]
    target = models[edit["part"]]
    original = next(row["depth_m"] for row in case["parts"] if row["name"] == edit["part"])
    for label, depth in (("edited", edit["depth_m"]), ("restored", original)):
        edit_depth(author, target, depth)
        for model in models.values():
            force_rebuild(author, model)
        metrics, loaded = measure_tree(author, root, case, paths, edited=label == "edited")
        require(set(loaded) == set(paths), "native root did not bind every authored dependency")
        result[label] = metrics
    saved = result["saved_files"] = {}
    for owner, model in models.items():
        saved[owner] = save_current(author, model, paths[owner], directory)
        require(all(int(author.get(models[key], "GetUpdateStamp")) == value["update_stamp"] and digest(paths[key]) == value["sha256"]
                    for key, value in saved.items()), "owner save changed already saved dependency bytes or update stamp")


def reopen_case(author, controller, case, paths, prior, result):
    root_path = paths[case["assemblies"][-1]["name"]]
    saved = prior["saved_files"]
    require(all(digest(paths[name]) == row["sha256"] for name, row in saved.items()), "nested source changed before its fresh reopen")
    root, errors, warnings = author.rec.call("open exact native nested root without preloading children", controller.open, root_path, read_only=True)
    result.update(open_errors=errors, open_warnings=warnings)
    require(root is not None and errors == warnings == 0 and exact_file(author.get(root, "GetPathName"), root_path), "native nested root failed or warned on fresh reopen")
    for label in ("initial", "rebuilt"):
        if label == "rebuilt":
            force_rebuild(author, root)
        scene, _ = measure_tree(author, root, case, paths)
        require(set(scene["definitions"]) == set(saved), "fresh source did not resolve every saved sibling")
        require(same_occurrences(scene["occurrences"], prior["restored"]["occurrences"]) and
                all(value["tree"] == prior["restored"]["definitions"][name]["tree"] for name, value in scene["definitions"].items()),
                "native nested hierarchy or feature tree changed on reopen")
        if label == "initial":
            require(all(value["update_stamp"] == saved[name]["update_stamp"] for name, value in scene["definitions"].items()), "native reopen did not bind exact persisted dependency stamps")
        result[label] = scene


def same_occurrences(actual, expected):
    keys = ("name", "target", "fixed", "configuration", "kind", "body_count")
    return len(actual) == len(expected) and all(
        all(first[key] == second[key] for key in keys) and matches_transform(first["world"], second["world"]) and
        same_occurrences(first["children"], second["children"]) for first, second in zip(actual, expected, strict=True)
    )


def phase(case, mode, root, seed, prior=None):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    case_dir = root / case["name"]
    directory = case_dir / "Author"
    if mode == "author":
        directory.mkdir(parents=True, exist_ok=False)
    paths = file_paths(directory, case)
    log_path = case_dir / ("Author.json" if mode == "author" else "Reopen.json")
    recorder = Recorder(log_path, {"case": case, "mode": mode})
    result = {"passed": False}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify executable version and SHA-256", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected SOLIDWORKS build")
            author = CurveAuthor(controller.app, recorder, Swapp)
            if prior is None:
                author_case(author, controller, case, paths, seed, directory, result)
            else:
                reopen_case(author, controller, case, paths, prior, result)
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = monitor.log
    saved = (prior or result).get("saved_files", {})
    result["native_files_match_persisted"] = bool(len(saved) == len(paths) and all(paths[key].is_file() and digest(paths[key]) == value["sha256"] for key, value in saved.items()))
    result["passed"] = bool(result["passed"] and result["native_files_match_persisted"] and not result["dialogs"] and not result.get("controller_diagnostics"))
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    result["record_sha256"] = digest(log_path)
    return result


def public_case(row):
    phases = row["phases"]
    records = {"name": row["name"], "split": row["split"], "records_sha256": [phase["record_sha256"] for phase in phases]}
    files = {key: {"sha256": value["sha256"], "bytes": value["bytes"]}
             for key, value in (phases[0].get("saved_files", {}) if phases else {}).items()}
    if row["split"] == "heldout":
        manifest = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        return records | {"native_file_manifest_sha256": sha256(manifest).hexdigest()}
    return records | {"passed": row["passed"], "native_files": files}


def run(deck_path, expected):
    from InspectFresh import healthy, inspect

    deck, disclosed, holdouts, seed = load_deck(deck_path, expected)
    specifications = cases_from(disclosed, "discovery") + cases_from(holdouts, "heldout")
    root = deck_path.parent / "Results"
    root.mkdir(exist_ok=False)
    private = root / "PrivateInspection.json"
    result = {"schema": "kit.sw2026.nested-assembly-source-observations.v1", "deck_sha256": expected,
              "started_at": time.time(), "cases": [], "controls": [], "passed": False}

    def checkpoint():
        write_json(private, result)

    def control(name):
        row = {"label": name}
        result["controls"].append(row)
        inspect(seed, result=row, checkpoint=checkpoint, parameter_names=PARAMETERS)
        row["passed"] = bool(healthy(row) and row.get("oracle_identity", {}).get("sha256") == ORACLE and row["sha256"] == CONTROL_SHA)
        checkpoint()
        return row

    try:
        if control("Before")["passed"]:
            for case in specifications:
                row = {"name": case["name"], "split": case["split"], "phases": [], "passed": False}
                result["cases"].append(row)
                first = phase(case, "author", root, seed)
                row["phases"].append(first)
                if first["passed"]:
                    row["phases"].append(phase(case, "reopen", root, seed, first))
                row["passed"] = len(row["phases"]) == 2 and all(item["passed"] for item in row["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            control("After")
        except Exception as error:
            result["final_control_exception"] = repr(error)
        processes = [row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["controls"]]
        processes.extend(row.get("oracle_identity", {}).get("process_creation_filetime") for case in result["cases"] for row in case["phases"])
        result["distinct_processes"] = len({item for item in processes if type(item) is int and item > 0})
        result["controls_healthy"] = [row.get("passed") for row in result["controls"]] == [True, True]
        result["deck_inputs_immutable"] = all(path.is_file() and digest(path) == sha for path, sha in
                                             ((seed, CONTROL_SHA), (disclosed, deck["discovery_sha256"]), (holdouts, deck["holdouts_sha256"])))
        result["passed"] = bool(result["controls_healthy"] and result["deck_inputs_immutable"] and len(processes) == result["distinct_processes"] == 10 and
                                len(result["cases"]) == 4 and all(row["passed"] for row in result["cases"]) and "exception" not in result)
        result["finished_at"] = time.time()
        checkpoint()
        write_json(root / "SourceLock.json", {
            "schema": "kit.sw2026.nested-assembly-source-lock.v1", "passed": result["passed"], "deck_sha256": expected,
            "control_sha256": CONTROL_SHA, "oracle_sha256": ORACLE, "oracle_file_version": "34.5.2.0604",
            "discovery_sha256": deck["discovery_sha256"], "holdouts_sha256": deck["holdouts_sha256"], "tools_sha256": deck["tool_hashes"],
            "controls_healthy": result["controls_healthy"], "deck_inputs_immutable": result["deck_inputs_immutable"],
            "distinct_processes": result["distinct_processes"], "private_inspection_sha256": digest(private),
            "writer_output_count": 0, "native_acceptance": False, "heldout_acceptance": False, "heldout_results_sealed": True,
            "cases": [public_case(row) for row in result["cases"]],
        })
    return result


def main():
    parser = argparse.ArgumentParser(description="Author and inspect a frozen nested native assembly source cohort")
    parser.add_argument("deck", type=Path)
    parser.add_argument("--deck-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.deck.resolve(strict=True)
    if args.verify_only:
        _, discovery, _, _ = load_deck(path, args.deck_sha256)
        cases_from(discovery, "discovery")
        print(json.dumps({"verified_source_deck": args.deck_sha256}))
        return 0
    result = run(path, args.deck_sha256)
    print(json.dumps({"passed": result["passed"], "distinct_processes": result["distinct_processes"], "controls_healthy": result["controls_healthy"], "writer_output_count": 0}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
