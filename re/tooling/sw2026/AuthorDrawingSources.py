from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import time
from pathlib import Path

import AuthorCurves as curves


def checked_file(path, expected, suffix):
    path = Path(path)
    curves.require(path.is_absolute() and path.suffix.lower() == suffix and path.is_file(), f"expected an absolute {suffix} input path")
    curves.require(curves.digest(path) == expected, f"{suffix} input hash differs")
    return path.resolve()


def vector(value, size, label):
    values = list(value)
    curves.require(len(values) == size and all(type(item) in (int, float) and math.isfinite(item) for item in values), f"{label} must contain {size} finite numbers")
    return values


def check_cases(specs):
    curves.require(specs["schema"] == "kit.sw2026.drawing-source-specs.v1", "wrong drawing specification version")
    cases = specs["cases"]
    curves.require(bool(cases) and len(cases) <= 24 and len(cases) == len({case["name"] for case in cases}), "drawing source names must be unique")
    for case in cases:
        pattern = {"discovery": r"D[0-9]{2}[A-Za-z]+", "heldout": r"H[0-9]{2}[A-Za-z]+"}.get(case["split"])
        curves.require(pattern is not None and re.fullmatch(pattern, case["name"]), "invalid drawing source name or split")
        view = case["view"]
        if view is not None:
            curves.require(view["orientation"] in ("*Front", "*Top", "*Right", "*Isometric"), "expected a standard model view")
            curves.require(all(value > 0 for value in vector(view["position_m"], 2, "view position")), "view position must be inside the sheet")
            curves.require(vector([view["scale"]], 1, "view scale")[0] > 0, "view scale must be positive")
    return cases


def read_job(job_path):
    job = json.loads(job_path.read_bytes())
    curves.require(job["schema"] == "kit.sw2026.drawing-source-job.v1", "wrong drawing source job version")
    curves.require(re.fullmatch(r"[a-f0-9]{40}", job["source_revision"]) is not None, "source revision must be a full Git SHA")
    curves.require(re.fullmatch(r"[a-f0-9]{64}", job["oracle_sha256"]) is not None, "oracle requires a pinned SHA-256")
    specs = checked_file(job["specs"], job["specs_sha256"], ".json")
    cases = check_cases(json.loads(specs.read_bytes()))
    control = checked_file(job["control"], job["control_sha256"], ".sldprt")
    template = checked_file(job["template"], job["template_sha256"], ".drwdot")
    reference = checked_file(job["reference_part"], job["reference_part_sha256"], ".sldprt")
    paper = job["paper_size"]
    curves.require(type(paper) is int and 0 <= paper < 12, "specify a standard native drawing paper-size enum")
    output = Path(job["output"])
    checkout = Path(job["checkout_root"])
    curves.require(checkout.is_absolute() and output.is_absolute() and not output.resolve().is_relative_to(checkout.resolve()), "drawing source output must be outside the checkout")
    return job, cases, (control, template, reference), output


def compare_values(author, label, actual, expected):
    for index, (value, target) in enumerate(zip(actual, expected, strict=True)):
        author.rec.close_number(f"{label} {index}", value, target)


def view_state(author, view, request, expected_child):
    child = author.get(view, "ReferencedDocument")
    curves.require(child is not None, "drawing view did not resolve its referenced part")
    child_path = Path(author.get(child, "GetPathName"))
    configuration = str(author.get(view, "ReferencedConfiguration"))
    active = author.get(author.get(child, "ConfigurationManager"), "ActiveConfiguration")
    curves.require(child_path.resolve() == expected_child.resolve(), "drawing view resolved the wrong child")
    curves.require(configuration and configuration == str(author.get(active, "Name")), "drawing view references the wrong configuration")
    part = author.typed(child, "PartDoc")
    curves.require(len(author.get(part, "GetBodies2", 0, True) or ()) == 1, "drawing view must resolve one visible solid body")
    mass = author.rec.call("measure drawing child mass", author.sw.mass, child)
    curves.require(isinstance(mass, dict) and mass.get("volume", 0) > 0 and mass.get("area", 0) > 0, "drawing child has no measurable solid geometry")
    orientation = str(author.get(view, "GetOrientationName"))
    curves.require(orientation == request["orientation"], "native view orientation differs")
    position = vector(author.get(view, "Position"), 2, "native view position")
    compare_values(author, "view position", position, request["position_m"])
    scale = float(author.get(view, "ScaleDecimal"))
    author.rec.close_number("view scale", scale, request["scale"])
    outline = vector(author.get(view, "GetOutline"), 4, "native view outline")
    curves.require(outline[0] < outline[2] and outline[1] < outline[3], "native model view outline is empty")
    transform = author.typed(author.get(view, "ModelToViewTransform"), "MathTransform")
    return {
        "name": str(author.get(view, "GetName2")), "orientation": orientation,
        "reference_name": str(author.get(view, "GetReferencedModelName")), "configuration": configuration,
        "position_m": position, "scale": scale, "outline_m": outline,
        "model_to_view": vector(author.get(transform, "ArrayData"), 16, "native model-to-view transform"),
        "child_volume_m3": mass["volume"], "child_area_m2": mass["area"],
        "child_center_m": vector(mass["com"], 3, "native child center of mass"),
        "child_update_stamp": int(author.get(child, "GetUpdateStamp")),
    }


def snapshot(author, model, drawing, request, child, paper):
    names = list(author.get(drawing, "GetSheetNames"))
    curves.require(len(names) == 1 and bool(names[0]), "drawing must have exactly one named sheet")
    sheet = author.typed(author.get(drawing, "GetCurrentSheet"), "Sheet")
    curves.require(str(author.get(sheet, "GetName")) == names[0], "current drawing sheet is inconsistent")
    properties = vector(author.get(sheet, "GetProperties2"), 8, "native sheet properties")
    curves.require(all(properties[index] > 0 for index in (2, 3, 5, 6)), "drawing sheet has no valid size or scale")
    curves.require(properties[0] == paper, "native drawing paper size differs")
    sheet_view = author.typed(author.get(drawing, "GetFirstView"), "View")
    raw_view = author.get(sheet_view, "GetNextView")
    curves.require((raw_view is None) == (request is None), "drawing model view count differs")
    problems = int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount"))
    curves.require(problems == 0, "drawing has native rebuild errors or warnings")
    result = {"sheet": names[0], "sheet_properties": properties, "whats_wrong": problems, "view": None}
    if raw_view is not None:
        curves.require(all(0 < position < size for position, size in zip(request["position_m"], properties[5:7], strict=True)), "requested model view center is outside the sheet")
        view = author.typed(raw_view, "View")
        curves.require(author.get(view, "GetNextView") is None, "drawing contains an unexpected second model view")
        result["view"] = view_state(author, view, request, child)
    return result


def compare_states(author, actual, expected):
    curves.require(actual["sheet"] == expected["sheet"], "drawing sheet identity changed")
    compare_values(author, "reopened sheet property", actual["sheet_properties"], expected["sheet_properties"])
    if actual["view"] is None:
        return
    current, saved = actual["view"], expected["view"]
    for field in ("name", "orientation", "reference_name", "configuration"):
        curves.require(current[field] == saved[field], f"drawing view {field} changed on reopen")
    for field in ("position_m", "outline_m", "model_to_view", "child_center_m"):
        compare_values(author, f"reopened {field}", current[field], saved[field])
    for field in ("scale", "child_volume_m3", "child_area_m2"):
        author.rec.close_number(f"reopened {field}", current[field], saved[field], absolute=1e-15)


def set_view_position(author, view, position):
    values = author.sw.VARIANT(author.sw.pythoncom.VT_ARRAY | author.sw.pythoncom.VT_R8, tuple(position))
    dynamic = author.sw.wc.dynamic.DumbDispatch(view)
    author.rec.call("set drawing view position", setattr, dynamic, "Position", values, parameters={"position_m": position})


def make_drawing(author, controller, template, paper, request, child):
    if child is not None:
        part, errors, warnings = author.rec.call("open immutable drawing reference", controller.open, child, read_only=True)
        curves.require(part is not None and errors == warnings == 0, "generated reference part did not open cleanly")
    model = author.get(controller.app, "NewDocument", str(template), paper, 0.0, 0.0)
    curves.require(model is not None, "native drawing template did not create a document")
    author.model = model
    drawing = author.typed(model, "DrawingDoc")
    if request is not None:
        x, y = request["position_m"]
        raw = author.get(drawing, "CreateDrawViewFromModelView3", str(child), request["orientation"], x, y, 0.0)
        curves.require(raw is not None, "native drawing did not create the requested model view")
        view = author.typed(raw, "View")
        author.set(view, "ScaleDecimal", request["scale"])
        set_view_position(author, view, request["position_m"])
    return drawing


def edit_position(author, model, drawing, request, child, paper, prior):
    sentinel = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sentinel, "GetNextView"), "View")
    dx, dy = 0.002731, -0.001739
    x, y = request["position_m"]
    position = [x + dx, y + dy]
    set_view_position(author, view, position)
    curves.require(bool(author.get(model, "EditRebuild3")), "edited drawing view rebuild failed")
    edited = snapshot(author, model, drawing, {**request, "position_m": position}, child, paper)
    outline = [value + delta for value, delta in zip(prior["view"]["outline_m"], (dx, dy, dx, dy), strict=True)]
    compare_values(author, "translated outline", edited["view"]["outline_m"], outline)
    return edited


def phase(sw, identify, case, name, output, job, template, reference, prior=None):
    directory = output / case["name"] / name
    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(directory / "Record.json", {"case": case, "phase": name})
    result = {"phase": name, "passed": False}
    controller = author = None
    request = case["view"]
    paper = job["paper_size"]
    path = output / case["name"] / "author" / (case["name"] + ".SLDDRW")
    child = path.parent / reference.name if request is not None else None
    with sw.Dismisser() as dialogs:
        try:
            rec.call("drawing source idle guard", sw.sweep)
            controller = rec.call("start fresh drawing oracle", sw.Sw, visible=True)
            identity = rec.call("verify drawing oracle identity", identify, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"] and controller.revision == "34.5.2", "drawing oracle identity differs")
            author = curves.CurveAuthor(controller.app, rec, sw)
            if prior is None:
                if child is not None:
                    rec.call("copy seed for oracle reference", shutil.copyfile, reference, child)
                    curves.require(curves.digest(child) == job["reference_part_sha256"], "drawing reference differs from its pinned seed")
                drawing = make_drawing(author, controller, template, paper, request, child)
            else:
                curves.require(curves.digest(path) == prior["native_sha256"], "locked drawing changed before reopen")
                curves.require(child is None or curves.digest(child) == job["reference_part_sha256"], "locked drawing reference changed before reopen")
                author.model, errors, warnings = rec.call("open locked drawing", controller.open, path, doctype=3, read_only=True)
                result.update(open_errors=errors, open_warnings=warnings)
                curves.require(author.model is not None and errors == warnings == 0, "locked drawing reopen failed or warned")
                drawing = author.typed(author.model, "DrawingDoc")
            result["initial"] = snapshot(author, author.model, drawing, request, child, paper)
            curves.require(bool(author.get(author.model, "ForceRebuild3", False)), "native drawing rebuild failed")
            result["rebuilt"] = snapshot(author, author.model, drawing, request, child, paper)
            if prior is None:
                result["save_status"] = rec.call("save independently authored drawing", controller.save_as, author.model, path)
                curves.require(result["save_status"] == (True, 0, 0), "drawing source save failed or warned")
                result.update(native_sha256=curves.digest(path), native_bytes=path.stat().st_size)
                result["saved"] = snapshot(author, author.model, drawing, request, child, paper)
            else:
                for state in ("initial", "rebuilt"):
                    compare_states(author, result[state], prior["saved"])
                if request is not None:
                    result["edited"] = edit_position(author, author.model, drawing, request, child, paper, result["rebuilt"])
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    rec.call("close owned drawing", controller.close_doc, author.model)
                    author.model = None
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    source = prior if prior is not None else result
    result["source_immutable"] = path.is_file() and curves.digest(path) == source.get("native_sha256")
    result["child_immutable"] = child is None or child.is_file() and curves.digest(child) == job["reference_part_sha256"]
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and result["source_immutable"] and result["child_immutable"] and not dialogs.log and not result.get("controller_diagnostics") and rec.data["first_failure"] is None and not rec.data["cleanup_errors"])
    rec.data.update(drawing_result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return {**result, "record_sha256": curves.digest(directory / "Record.json"), "numeric_checks": len(rec.data["checks"])}


def freeze(job_path):
    job, cases, inputs, output = read_job(job_path)
    control, template, reference = inputs
    import Swapp
    from InspectFresh import healthy, inspect
    from OracleIdentity import application_identity

    output.mkdir(parents=True, exist_ok=False)
    public = {key: job[key] for key in ("source_revision", "specs_sha256", "oracle_sha256", "control_sha256", "template_sha256", "reference_part_sha256", "paper_size")}
    related_tools = {**curves.tool_hashes(), "InspectFresh.py": curves.digest(Path(__file__).with_name("InspectFresh.py"))}
    public.update(schema="kit.sw2026.drawing-source-lock.v1", job_sha256=curves.digest(job_path), tool_sha256=curves.digest(Path(__file__)), related_tool_hashes=related_tools, started_at=time.time(), writer_output_count=0, native_acceptance=False, heldout_acceptance=False)
    private = {**public, "cases": [], "controls": []}

    def checkpoint():
        curves.write_json(output / "PrivateInspection.json", private)

    def control_phase(name):
        row = {"kind": name}
        private["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = healthy(row) and row["oracle_identity"]["sha256"] == job["oracle_sha256"]
        checkpoint()
        return row

    try:
        if control_phase("control_before")["healthy"]:
            for case in cases:
                row = {"name": case["name"], "split": case["split"], "has_model_view": case["view"] is not None, "phases": []}
                private["cases"].append(row)
                authored = phase(Swapp, application_identity, case, "author", output, job, template, reference)
                row["phases"].append(authored)
                if authored["passed"]:
                    row["phases"].append(phase(Swapp, application_identity, case, "fresh-reopen", output, job, template, reference, authored))
                row["passed"] = len(row["phases"]) == 2 and all(value["passed"] for value in row["phases"])
                checkpoint()
    except Exception as error:
        private["exception"] = repr(error)
    finally:
        try:
            control_phase("control_after")
        except Exception as error:
            private["control_after_exception"] = repr(error)
        rows = [*private["controls"], *(value for case in private["cases"] for value in case["phases"])]
        processes = [row["oracle_identity"]["process_creation_filetime"] for row in rows if "oracle_identity" in row]
        controls = [row.get("healthy", False) for row in private["controls"]]
        immutable = all(path.is_file() and curves.digest(path) == job[name + "_sha256"] for path, name in zip(inputs, ("control", "template", "reference_part"), strict=True))
        passed = len(processes) == len(set(processes)) == 2 + 2 * len(cases) and controls == [True, True] and immutable and len(private["cases"]) == len(cases) and all(row.get("passed") for row in private["cases"]) and "exception" not in private
        private.update(passed=passed, control_results=controls, pinned_inputs_immutable=immutable, distinct_processes=len(set(processes)), finished_at=time.time())
        checkpoint()
        public.update({key: private[key] for key in ("passed", "control_results", "pinned_inputs_immutable", "distinct_processes", "finished_at")})
        public["private_inspection_sha256"] = curves.digest(output / "PrivateInspection.json")
        public["cases"] = [
            {"name": row["name"], "split": row["split"], "passed": row.get("passed", False),
             "native_sha256": authored.get("native_sha256"), "native_bytes": authored.get("native_bytes"),
             "reference_part_sha256": job["reference_part_sha256"] if row["has_model_view"] else None,
             "record_sha256": [value["record_sha256"] for value in row["phases"]],
             "numeric_checks": sum(value["numeric_checks"] for value in row["phases"])}
            for row in private["cases"] for authored in (row["phases"][0] if row["phases"] else {},)
        ]
        curves.write_json(output / "SourceLock.json", public)
    print(json.dumps({"passed": passed, "sources": len(public["cases"]), "native_acceptance": False}))
    return 0 if passed else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Author and lock drawing research sources in the SOLIDWORKS 2026 oracle")
    parser.add_argument("job", type=Path)
    args = parser.parse_args(argv)
    return freeze(args.job)


if __name__ == "__main__":
    raise SystemExit(main())
