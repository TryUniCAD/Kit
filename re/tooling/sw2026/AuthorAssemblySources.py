from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectCircleSketch import digest
from InspectFresh import healthy, inspect
from ObserveAssemblyLoad import AssemblyLoadMonitor
from OracleIdentity import application_identity


def placement_transform(placement):
    axis = "xyz".index(placement["axis"])
    angle = math.radians(placement["angle_deg"])
    translation = placement["translation_m"]
    AuthorCurves.require(len(translation) == 3 and all(math.isfinite(v) for v in (angle, *translation)), "invalid assembly placement")
    basis = [0.0] * 9
    first, second = (axis + 1) % 3, (axis + 2) % 3
    basis[axis * 3 + axis] = 1.0
    basis[first * 3 + first] = basis[second * 3 + second] = math.cos(angle)
    basis[first * 3 + second] = math.sin(angle)
    basis[second * 3 + first] = -math.sin(angle)
    return [*basis, *translation, 1.0, 0.0, 0.0, 0.0]


def transform_point(transform, point):
    return [sum(point[row] * transform[row * 3 + col] for row in range(3)) + transform[9 + col] for col in range(3)]


def feature_tree(author, model):
    rows, visited = [], set()

    def visit(feature, parent):
        siblings = 0
        while feature is not None:
            siblings += 1
            AuthorCurves.require(siblings <= 256 and len(rows) < 512, "assembly feature traversal exceeded its bound")
            name = str(author.get(feature, "Name"))
            kind = str(author.get(feature, "GetTypeName2"))
            key = (name, kind)
            if key not in visited:
                visited.add(key)
                warning = Swapp.byref_bool()
                raw = author.get(feature, "GetErrorCode2", warning)
                code, warned = (int(raw[0]), bool(raw[1])) if isinstance(raw, tuple) else (int(raw), bool(warning.value))
                rows.append({"name": name, "type": kind, "parent": parent, "error": code, "warning": warned, "suppressed": bool(author.get(feature, "IsSuppressed"))})
                AuthorCurves.require(code == 0 and not warned, "assembly feature has an error or warning")
                visit(author.get(feature, "GetFirstSubFeature"), name)
            feature = author.get(feature, "GetNextFeature" if parent is None else "GetNextSubFeature")

    visit(author.get(model, "FirstFeature"), None)
    AuthorCurves.require(bool(rows), "native assembly feature tree is empty")
    return rows


def transform_matches(actual, expected):
    return len(actual) == len(expected) == 16 and all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) for a, b in zip(actual, expected, strict=True))


def snapshot(author, model, assembly, expected, control, control_mass, label):
    all_count = int(author.get(assembly, "GetComponentCount", False))
    top_count = int(author.get(assembly, "GetComponentCount", True))
    components = author.get(assembly, "GetComponents", True) or ()
    AuthorCurves.require(all_count == top_count == len(components) == len(expected), "assembly occurrence count or nesting differs")
    rows = []
    used = set()
    for raw in components:
        component = author.typed(raw, "Component2")
        path = Path(str(author.get(component, "GetPathName")))
        AuthorCurves.require(path.resolve() == control.resolve(), "assembly occurrence resolves to the wrong child")
        transform = author.typed(author.get(component, "Transform2"), "MathTransform")
        values = [float(v) for v in author.get(transform, "ArrayData")]
        matches = [index for index, request in enumerate(expected) if transform_matches(values, request)]
        AuthorCurves.require(len(matches) == 1 and matches[0] not in used, "assembly occurrence transform does not uniquely match a requested placement")
        index = matches[0]
        used.add(index)
        for offset, target in enumerate(expected[index]):
            author.rec.close_number(f"{label} occurrence {index} transform {offset}", values[offset], target)
        child = author.get(component, "GetModelDoc2")
        AuthorCurves.require(child is not None, "assembly child is not resolved")
        part = author.typed(child, "PartDoc")
        bodies = len(author.get(part, "GetBodies2", 0, True) or ())
        AuthorCurves.require(bodies == 1 and not author.get(component, "IsSuppressed"), "assembly occurrence is suppressed or has no visible solid child")
        rows.append({"placement_index": index, "name": str(author.get(component, "Name2")), "path_basename": path.name, "configuration": str(author.get(component, "ReferencedConfiguration")), "fixed": bool(author.get(component, "IsFixed")), "transform": values, "visible_child_bodies": bodies})
    result = {"top_level_count": top_count, "total_count": all_count, "occurrences": sorted(rows, key=lambda row: row["placement_index"]), "body_count": sum(row["visible_child_bodies"] for row in rows), "tree": feature_tree(author, model)}
    AuthorCurves.require(int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount")) == 0, "native assembly reports rebuild problems")
    if expected:
        mass = author.rec.call("read assembly mass properties in system units", Swapp.mass, model)
        AuthorCurves.require(isinstance(mass, dict) and "error" not in mass, "native assembly has no mass properties")
        for key in ("volume", "area"):
            author.rec.close_number(f"{label} assembly {key}", mass[key], len(expected) * control_mass[key], absolute=1e-15)
        centers = [transform_point(matrix, control_mass["com"]) for matrix in expected]
        for index in range(3):
            author.rec.close_number(f"{label} assembly center {index}", mass["com"][index], sum(center[index] for center in centers) / len(centers), absolute=1e-15)
        result["mass"] = mass
    return result


def run_phase(case, phase, output, job, control, control_mass, prior=None):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    recorder = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    result = {"phase": phase, "passed": False}
    controller = model = None
    with AssemblyLoadMonitor() as dialogs:
        try:
            recorder.call("assembly source idle guard", Swapp.sweep)
            controller = recorder.call("start fresh owned assembly oracle", Swapp.Sw)
            identity = recorder.call("verify assembly oracle build", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"] and controller.revision == "34.5.2", "assembly oracle build differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, recorder, Swapp)
            expected = [placement_transform(placement) for placement in case["placements"]]
            if prior is None:
                template = Path(recorder.call("read registered assembly template location", controller.template, "assembly"))
                AuthorCurves.require(template.is_absolute() and template.suffix.lower() == ".asmdot" and template.is_file(), "registered native assembly template is missing")
                result["oracle_template_sha256"] = digest(template)
                model = author.get(controller.app, "NewDocument", str(template), 0, 0, 0)
                AuthorCurves.require(model is not None, "native assembly document creation failed")
                assembly = author.typed(model, "AssemblyDoc")
                if expected:
                    names = [str(control)] * len(expected)
                    transforms = [v for row in expected for v in row]
                    origins = [""] * len(expected)
                    variants = [Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | kind, value) for kind, value in ((Swapp.pythoncom.VT_BSTR, names), (Swapp.pythoncom.VT_R8, transforms), (Swapp.pythoncom.VT_BSTR, origins))]
                    values = recorder.call("AddComponents3", assembly.AddComponents3, *variants, parameters={"names": names, "transforms": transforms, "coordinate_system_names": origins})
                    AuthorCurves.require(values is not None and len(values) == len(expected), "native assembly insertion count differs")
                path = directory / (case["name"] + ".SLDASM")
            else:
                path = Path(prior["native_path"])
                AuthorCurves.require(digest(path) == prior["native_sha256"], "locked assembly source changed before reopen")
                model, errors, warnings = recorder.call("open locked assembly source", controller.open, path, read_only=True)
                result.update(open_errors=errors, open_warnings=warnings)
                AuthorCurves.require(model is not None and errors == warnings == 0, "assembly source reopen failed or warned")
                assembly = author.typed(model, "AssemblyDoc")
            result["initial"] = snapshot(author, model, assembly, expected, control, control_mass, "initial")
            AuthorCurves.require(bool(author.get(model, "ForceRebuild3", False)), "assembly source rebuild failed")
            result["rebuilt"] = snapshot(author, model, assembly, expected, control, control_mass, "rebuilt")
            if prior is None:
                status = recorder.call("save native assembly source", controller.save_as, model, path)
                AuthorCurves.require(status == (True, 0, 0), "native assembly source save failed or warned")
                result["saved"] = snapshot(author, model, assembly, expected, control, control_mass, "saved")
                result.update(native_path=str(path), native_sha256=digest(path), native_bytes=path.stat().st_size)
            else:
                for name in ("initial", "rebuilt"):
                    keys = ("name", "path_basename", "configuration", "fixed", "visible_child_bodies")
                    actual = [[item[key] for key in keys] for item in result[name]["occurrences"]]
                    saved = [[item[key] for key in keys] for item in prior["saved"]["occurrences"]]
                    AuthorCurves.require(actual == saved, "assembly occurrence identity or state changed across reopen")
                result["source_immutable"] = digest(path) == prior["native_sha256"]
                AuthorCurves.require(result["source_immutable"], "assembly source changed on reopen")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if model is not None:
                try:
                    recorder.call("close owned assembly document", controller.close_doc, model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    if prior is not None:
        result["source_immutable"] = digest(Path(prior["native_path"])) == prior["native_sha256"]
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and result.get("source_immutable", True) and not result["dialogs"] and not result.get("controller_diagnostics") and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(assembly_result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    result.update(record_sha256=digest(directory / "Record.json"), numeric_checks=len(recorder.data["checks"]))
    return result


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    specs_path = Path(job["specs"])
    AuthorCurves.require(job["schema"] == "kit.sw2026.ordinary-assembly-job.v1" and digest(specs_path) == job["specs_sha256"], "assembly source job or specification identity differs")
    specs = json.loads(specs_path.read_bytes())
    cases = specs["cases"]
    AuthorCurves.require(specs["schema"] == "kit.sw2026.ordinary-assembly-specs.v1" and len(cases) == len({c["name"] for c in cases}) == 5 and [c["split"] for c in cases] == ["discovery"] * 3 + ["heldout"] * 2, "assembly source case membership differs")
    AuthorCurves.require(all(re.fullmatch(r"A[0-9]{2}[A-Za-z]+", c["name"]) for c in cases if c["split"] == "discovery") and all(re.fullmatch(r"A[0-9]{2}Heldout[A-Za-z]+", c["name"]) for c in cases if c["split"] == "heldout"), "invalid assembly source names")
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "assembly native control changed")
    output = Path(job["output"])
    AuthorCurves.require(output.is_absolute() and not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()), "assembly source output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "kit.sw2026.ordinary-assembly-source.v1", "source_revision": job["source_revision"], "specs_sha256": digest(specs_path), "tool_sha256": digest(Path(__file__)), "job_sha256": digest(job_path), "started_at": time.time(), "cases": [], "controls": [], "passed": False}

    def checkpoint():
        AuthorCurves.write_json(output / "PrivateInspection.json", result)

    def control_phase(name):
        row = {"kind": name}
        result["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = healthy(row) and row["oracle_identity"]["sha256"] == job["oracle_sha256"]
        checkpoint()
        return row

    try:
        before = control_phase("control_before")
        if before["healthy"]:
            for case in cases:
                row = {"name": case["name"], "split": case["split"], "phases": []}
                result["cases"].append(row)
                first = run_phase(case, "author", output, job, control, before["mass"])
                row["phases"].append(first)
                if first["passed"]:
                    row["phases"].append(run_phase(case, "fresh-reopen", output, job, control, before["mass"], first))
                identities = [p["oracle_identity"]["process_creation_filetime"] for p in row["phases"] if "oracle_identity" in p]
                row["fresh_processes"] = len(identities) == len(set(identities)) == 2
                row["passed"] = row["fresh_processes"] and all(p["passed"] for p in row["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        control_phase("control_after")
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        identities = [phase["oracle_identity"]["process_creation_filetime"] for row in result["cases"] for phase in row["phases"] if "oracle_identity" in phase]
        identities.extend(row["oracle_identity"]["process_creation_filetime"] for row in result["controls"] if "oracle_identity" in row)
        result["distinct_processes"] = len(set(identities))
        result["passed"] = bool(result["controls_healthy"] and result["control_immutable"] and len(identities) == result["distinct_processes"] == 12 and len(result["cases"]) == len(cases) and all(row["passed"] for row in result["cases"]) and not result.get("exception"))
        result["finished_at"] = time.time()
        checkpoint()
        lock = {key: result[key] for key in ("passed", "source_revision", "job_sha256", "specs_sha256", "tool_sha256", "controls_healthy", "control_immutable", "distinct_processes", "started_at", "finished_at")}
        lock.update(schema="kit.sw2026.ordinary-assembly-source-lock.v1", control_sha256=job["control_sha256"], private_inspection_sha256=digest(output / "PrivateInspection.json"), writer_output_count=0, native_acceptance=False, heldout_acceptance=False, heldout_results_sealed=True, cases=[])
        for row in result["cases"]:
            first = row["phases"][0] if row["phases"] else {}
            lock["cases"].append({"name": row["name"], "split": row["split"], "passed": row.get("passed", False), "native_sha256": first.get("native_sha256"), "native_bytes": first.get("native_bytes"), "phases": len(row["phases"]), "record_sha256": [phase["record_sha256"] for phase in row["phases"]], "numeric_checks": sum(phase["numeric_checks"] for phase in row["phases"])})
        AuthorCurves.write_json(output / "SourceLock.json", lock)
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "controls_healthy": result["controls_healthy"], "writer_output_count": 0}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
