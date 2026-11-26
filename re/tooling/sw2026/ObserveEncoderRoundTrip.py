from argparse import ArgumentParser
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback


CASES = {
    "Baseline": (
        ((-0.013, -0.003), (0.008, -0.009), (0.019, 0.006), (0.004, 0.023)),
        0.01431,
        0.01987,
    ),
    "HeldOut": (
        ((-0.016, 0.004), (-0.009, -0.012), (0.012, -0.010),
         (0.021, 0.002), (0.017, 0.015), (0.002, 0.011), (-0.004, 0.019)),
        0.00973,
        0.01219,
    ),
}
MATERIAL_DENSITY = 7  # swMaterialPropertyDensity


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(path):
    with path.open("rb") as stream:
        return sha256(stream.read()).hexdigest()


def record(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def member(owner, name):
    from win32com.client.dynamic import CDispatch

    value = getattr(owner, name)
    return value() if callable(value) and not isinstance(value, CDispatch) else value


def statuses():
    import pythoncom
    from win32com.client import VARIANT

    return tuple(
        VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0) for _ in range(2)
    )


def save(document, path):
    import pythoncom
    from win32com.client import VARIANT

    require(not path.exists(), "save destination already exists")
    errors, warnings = statuses()
    saved = document.Extension.SaveAs(
        str(path), 0, 1, VARIANT(pythoncom.VT_DISPATCH, None), errors, warnings,
    )
    result = {"saved": bool(saved), "errors": errors.value, "warnings": warnings.value}
    require(saved and errors.value == warnings.value == 0 and path.is_file(), str(result))
    return result


def author(app, template, path, points, depth):
    document = app.NewDocument(str(template), 0, 0.0, 0.0)
    require(document is not None, "SOLIDWORKS could not create a part from its template")
    try:
        plane = document.FeatureByName("Front Plane")
        require(plane is not None and plane.Select2(False, 0), "Front Plane selection failed")
        manager = document.SketchManager
        manager.InsertSketch(True)
        manager.AddToDB = True
        try:
            for start, end in zip(points, (*points[1:], points[0]), strict=True):
                require(manager.CreateLine(*start, 0, *end, 0) is not None, "sketch line creation failed")
        finally:
            manager.AddToDB = False
        manager.InsertSketch(True)
        document.ClearSelection2(True)
        sketch = document.FeatureByName("Sketch1")
        require(sketch is not None and sketch.Select2(False, 0), "sketch selection failed")
        args = (
            True, False, False, 0, 0, depth, 0.0, False, False, False, False,
            0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False,
        )
        boss = document.FeatureManager.FeatureExtrusion3(*args)
        require(boss is not None, "blind boss creation failed")
        boss.Name = "Boss-Extrude1"
        require(document.ForceRebuild3(False), "authored part did not rebuild")
        observation = inspect(document)
        status = save(document, path)
        return {"body": observation, "save_status": status, "extrusion_args": args}
    finally:
        app.QuitDoc(str(member(document, "GetTitle")))


def inspect(document):
    import pythoncom
    from win32com.client import VARIANT

    tree = []
    feature = member(document, "FirstFeature")
    while feature is not None:
        require(len(tree) < 128, "feature tree exceeds the bounded part scope")
        warning = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
        row = {
            "name": str(feature.Name),
            "type": member(feature, "GetTypeName2"),
            "suppressed": bool(member(feature, "IsSuppressed")),
            "status": int(feature.GetErrorCode2(warning)),
            "warning": bool(warning.value),
        }
        tree.append(row)
        feature = member(feature, "GetNextFeature")
    sketch = member(document.FeatureByName("Sketch1"), "GetSpecificFeature2")
    segments = member(sketch, "GetSketchSegments") or ()
    entities = []
    for segment in segments:
        first = member(segment, "GetStartPoint2")
        second = member(segment, "GetEndPoint2")
        entities.append({"kind": int(member(segment, "GetType")), "points": [(point.X, point.Y, point.Z) for point in (first, second)]})
    relations = sketch.RelationManager.GetRelations(0) or ()
    bodies = document.GetBodies2(0, False) or ()
    require(len(bodies) == 1, f"expected one solid, found {len(bodies)}")
    body, = bodies
    properties = body.GetMassProperties(1.0)
    mass = member(document.Extension, "CreateMassProperty")
    require(mass is not None, "native mass property service is unavailable")
    dimension = document.Parameter("D1@Boss-Extrude1")
    require(dimension is not None, "driving D1 does not exist")
    return {
        "bodies": len(bodies), "tree": tree, "sketch_segments": entities,
        "sketch_relations": len(relations), "depth_m": float(dimension.SystemValue),
        "dimension_driving": int(dimension.DrivenState) == 2,
        "volume_m3": float(properties[3]), "area_m2": float(properties[4]),
        "centre_of_mass_m": list(properties[:3]), "mass_kg": float(properties[5]),
        "document_density_kg_m3": float(document.Extension.GetUserPreferenceDouble(MATERIAL_DENSITY, 0)),
        "effective_density_kg_m3": float(mass.Density),
        "faces": int(member(body, "GetFaceCount")), "edges": int(member(body, "GetEdgeCount")),
        "vertices": len(member(body, "GetVertices") or ()),
    }


def open_part(app, path, result, edit, derivative):
    errors, warnings = statuses()
    document = app.OpenDoc6(str(path), 1, 1, "", errors, warnings)
    result.update(open_errors=errors.value, open_warnings=warnings.value)
    require(document is not None, f"SOLIDWORKS failed to open the part: {errors.value}")
    try:
        require(errors.value == warnings.value == 0, "SOLIDWORKS reported load errors or warnings")
        result["states"]["Initial"] = inspect(document)
        require(document.ForceRebuild3(False), "unchanged part did not rebuild")
        result["states"]["Rebuilt"] = inspect(document)
        if edit is not None:
            document.Parameter("D1@Boss-Extrude1").SystemValue = edit
            require(document.ForceRebuild3(False), "edited part did not rebuild")
            result["states"]["Edited"] = inspect(document)
            result["save_status"] = save(document, derivative)
            result["derivative_sha256"] = digest(derivative)
    finally:
        app.QuitDoc(str(member(document, "GetTitle")))


def phase(root, request, output):
    import pythoncom
    import win32api
    from win32com.client import DispatchEx

    sys.path.insert(0, str(root / "re/automation/ApplicationWorkers"))
    from SolidWorksAvailability import HoldMutex, IsSolidWorksRunning, OracleMutex
    from WindowsIdentity import process_start
    from WindowsProcessExit import observe_exit, watch_peer

    binary = Path(request["executable"]).resolve(strict=True)
    result = {"role": request["role"], "passed": False, "states": {}}
    try:
        require(digest(binary) == request["executable_sha256"], "oracle executable digest differs")
        version = win32api.GetFileVersionInfo(str(binary), "\\")
        high, low = version["FileVersionMS"], version["FileVersionLS"]
        build = f"{high >> 16}.{high & 65535}.{low >> 16}.{low & 65535:04}"
        with HoldMutex(OracleMutex) as held:
            require(held and not IsSolidWorksRunning(), "oracle leased or SOLIDWORKS already running")
            pythoncom.CoInitialize()
            try:
                app = DispatchEx("SldWorks.Application")
                pid = int(member(app, "GetProcessID"))
                peer = {"pid": pid, "started": process_start(pid)}
                with watch_peer(peer, binary) as watch:
                    require(not member(app, "GetDocumentCount"), "new SOLIDWORKS process contains a document")
                    result["oracle_identity"] = {
                        **peer, "revision": str(member(app, "RevisionNumber")), "build": build,
                        "sha256": digest(binary),
                    }
                    try:
                        app.UserControlBackground = True
                        require(app.UserControlBackground, "could not retain owned background session")
                        if request["operation"] == "author":
                            folder = output.parent
                            result["template_sha256"] = digest(Path(request["template"]))
                            result["length_units"] = "m"
                            result["authored"] = {}
                            for name, (points, first, edited) in CASES.items():
                                for tag, depth in (("Source", first), ("EditedControl", edited)):
                                    native = folder / f"{name}{tag}.SLDPRT"
                                    row = author(app, Path(request["template"]), native, points, depth)
                                    result["authored"][native.name] = {
                                        **row, "sha256": digest(native), "profile_m": points, "depth_m": depth,
                                    }
                        else:
                            source = Path(request["source"]).resolve(strict=True)
                            result["source_sha256"] = digest(source)
                            require(result["source_sha256"] == request["source_sha256"], "phase input differs")
                            edit = request.get("edit_depth_m")
                            open_part(app, source, result, edit, output.parent / "Edited.SLDPRT")
                            require(digest(source) == result["source_sha256"], "phase input changed")
                    finally:
                        if not member(app, "GetDocumentCount"):
                            app.ExitApp()
                            del app
                            result["exit"] = observe_exit(watch, 30000)
                        else:
                            result["cleanup_error"] = "owned process retained a document"
                require(result.get("exit") and result["exit"]["exit_code"] == 0, "normal owned exit was not observed")
            finally:
                pythoncom.CoUninitialize()
        result["passed"] = True
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
        traceback.print_exc()
    record(output, result)
    return 0 if result["passed"] else 1


def run_phase(args, phase_dir, label, request):
    phase_dir.mkdir()
    supplied = {
        **request, "role": label, "executable": str(args.executable.resolve(strict=True)),
        "executable_sha256": args.executable_sha256,
    }
    request_path = phase_dir / "Request.json"
    response_path = phase_dir / "Record.json"
    record(request_path, supplied)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(args.root),
               "phase", str(request_path), str(response_path)]
    with (phase_dir / "Worker.log").open("xb") as log:
        try:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False)
        except subprocess.TimeoutExpired:
            return {"role": label, "passed": False, "error": "native worker exceeded 180 seconds"}
    if not response_path.is_file():
        return {"role": label, "passed": False, "error": "native worker produced no record", "exit_code": process.returncode}
    result = json.loads(response_path.read_bytes())
    return {**result, "record_sha256": digest(response_path), "worker_exit_code": process.returncode}


def expected_profile(points, depth):
    pairs = tuple(zip(points, (*points[1:], points[0]), strict=True))
    products = [x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in pairs]
    area = math.fsum(products) / 2
    centre_x = math.fsum((first[0] + second[0]) * cross for (first, second), cross in zip(pairs, products, strict=True))
    centre_y = math.fsum((first[1] + second[1]) * cross for (first, second), cross in zip(pairs, products, strict=True))
    return {
        "depth_m": depth,
        "volume_m3": abs(area) * depth,
        "area_m2": 2 * abs(area) + sum(math.dist(*pair) for pair in pairs) * depth,
        "centre_of_mass_m": [centre_x / (6 * area), centre_y / (6 * area), depth / 2],
        "faces": len(points) + 2,
        "edges": len(points) * 3,
        "vertices": len(points) * 2,
    }


def compare_observation(state, points, depth, reference=None):
    expected = expected_profile(points, depth)
    numbers = ("depth_m", "volume_m3", "area_m2", "faces", "edges", "vertices")
    actual_mass = (*[state[key] for key in numbers], *state["centre_of_mass_m"])
    expected_mass = (*[expected[key] for key in numbers], *expected["centre_of_mass_m"])
    require(state["dimension_driving"] and state["bodies"] == 1, "expected one solid driven by D1")
    require(
        math.isfinite(state["document_density_kg_m3"]) and state["document_density_kg_m3"] > 0
        and math.isfinite(state["effective_density_kg_m3"]) and state["effective_density_kg_m3"] > 0,
        "native density measurement is unavailable",
    )
    require(
        all(math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-12)
            for left, right in zip(actual_mass, expected_mass, strict=True)),
        f"prism measurements differ: {actual_mass!r} against {expected_mass!r}",
    )
    require(state["sketch_relations"] == 0, "unexpected profile relations")
    require(all(row["status"] == 0 and not row["warning"] for row in state["tree"]), "feature tree reports errors")
    model_rows = [row for row in state["tree"] if row["type"] in ("RefPlane", "OriginProfileFeature", "ProfileFeature", "Extrusion", "Boss")]
    require(
        [row["name"] for row in model_rows] == ["Front Plane", "Top Plane", "Right Plane", "Origin", "Sketch1", "Boss-Extrude1"]
        and not any(row["suppressed"] for row in model_rows),
        f"unexpected parametric tree: {model_rows!r}",
    )
    actual_segments = sorted(
        tuple(sorted(tuple(round(coord, 12) for coord in point) for point in segment["points"]))
        for segment in state["sketch_segments"]
    )
    expected_segments = sorted(
        tuple(sorted(((start[0], start[1], 0), (end[0], end[1], 0))))
        for start, end in zip(points, (*points[1:], points[0]), strict=True)
    )
    require(
        all(segment["kind"] == 0 for segment in state["sketch_segments"])
        and actual_segments == expected_segments,
        f"line profile differs: {actual_segments!r} against {expected_segments!r}",
    )
    if reference is not None:
        require(
            [row for row in reference["tree"] if row["name"] in {item["name"] for item in model_rows}] == model_rows,
            "candidate parametric tree differs from the independent vendor control",
        )
        reference_values = (*[reference[key] for key in numbers], *reference["centre_of_mass_m"])
        require(
            all(math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-12)
                for left, right in zip(actual_mass, reference_values, strict=True)),
            "candidate prism differs from the independent vendor control",
        )
        require(
            all(math.isclose(state[key], reference[key], rel_tol=1e-8, abs_tol=1e-12)
                for key in ("document_density_kg_m3", "effective_density_kg_m3")),
            "candidate density differs from the independent vendor control",
        )
    return len(actual_mass) if reference is None else len(actual_mass) * 2 + 2


def measure(args):
    points, original, edited = CASES[args.case]
    initial_depth, edit_depth = (edited, original) if args.edited else (original, edited)
    control, other_control = (args.edited_control, args.control) if args.edited else (args.control, args.edited_control)
    candidate = args.candidate.resolve(strict=True)
    candidate_sha = digest(candidate)
    locator, manifest_sha = None, None
    if args.candidate_manifest:
        manifest_sha = digest(args.candidate_manifest)
        manifest = json.loads(args.candidate_manifest.read_bytes())
        require(
            manifest["stage"] == "awaiting_native_measurement"
            and manifest["archive_sha256"] == candidate_sha
            and manifest["archive_bytes"] == candidate.stat().st_size
            and manifest["runtime_input_reads"] == 0,
            "native input differs from its guarded preparation custody",
        )
        locator = Path(manifest["native_locator"])
        require(locator.is_absolute() and not locator.exists(), "encoded output locator is already present")
    args.output.mkdir()
    phases = {}
    faults = {}

    def observe(label, source, edit=None):
        source = source.resolve(strict=True)
        outcome = run_phase(args, args.output / label, label, {
            "operation": "measure", "source": str(source), "source_sha256": digest(source),
            "edit_depth_m": edit,
        })
        phases[label] = outcome
        if not outcome["passed"]:
            faults[label] = outcome.get("error", "native phase failed")
        return outcome

    before = observe("ControlBefore", control)
    opposite = observe("EditControl", other_control) if before["passed"] else None
    if opposite and opposite["passed"]:
        generated = observe("CandidateGenerated", candidate, edit_depth)
        if generated["passed"]:
            derivative = args.output / "CandidateGenerated/Edited.SLDPRT"
            require(digest(derivative) == generated["derivative_sha256"], "edited derivative changed")
            observe("CandidateReopen", derivative)
    observe("ControlAfter", control)
    if locator is not None and locator.exists():
        faults["custody"] = "encoded output locator appeared during measurement"
    if digest(candidate) != candidate_sha:
        faults["custody"] = "candidate changed during measurement"
    checks = {}
    reference_depths = {"ControlBefore": initial_depth, "ControlAfter": initial_depth, "EditControl": edit_depth}
    for label, item in phases.items():
        if not item["passed"]:
            continue
        try:
            checks[label] = 0
            for state_name, state in item["states"].items():
                state_depth = reference_depths.get(label)
                reference = None
                if state_depth is None:
                    is_edited = label == "CandidateReopen" or state_name == "Edited"
                    state_depth = edit_depth if is_edited else initial_depth
                    reference = phases["EditControl" if is_edited else "ControlBefore"]["states"]["Rebuilt"]
                checks[label] += compare_observation(state, points, state_depth, reference)
            if label == "CandidateReopen":
                require(
                    item["states"]["Rebuilt"]["tree"] == phases["CandidateGenerated"]["states"]["Edited"]["tree"],
                    "saved edit reopened with a different feature tree",
                )
        except ValueError as error:
            faults[label] = str(error)
    lifetimes = [
        (item["oracle_identity"]["pid"], item["oracle_identity"]["started"])
        for item in phases.values() if "oracle_identity" in item
    ]
    require(len(lifetimes) == len(set(lifetimes)), "native phases reused a process")
    result = {
        "schema": "kit.sw2026.encoder-round-trip-native-observation.v1",
        "case": args.case, "edited_input": args.edited, "method_sha256": digest(Path(__file__)),
        "candidate_sha256": candidate_sha, "candidate_manifest_sha256": manifest_sha,
        "archive_locator_absent": locator is not None and "custody" not in faults,
        "passed": len(phases) == 5 and not faults,
        "controls_healthy": all(label in phases and label not in faults for label in reference_depths),
        "distinct_native_processes": len(lifetimes), "numeric_checks": checks, "faults": faults,
        "phases": phases,
    }
    report = args.output / "Result.json"
    record(report, result)
    print(json.dumps({key: value for key, value in result.items() if key != "phases"}))
    return 0 if result["passed"] else 1


def main(argv=None):
    default_root = Path(__file__).resolve().parents[3]
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, default=default_root)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("author", "measure"):
        command = modes.add_parser(mode)
        command.add_argument("--executable", type=Path, required=True)
        command.add_argument("--executable-sha256", required=True)
        command.add_argument("--output", type=Path, required=True)
        if mode == "author":
            command.add_argument("--template", type=Path, required=True)
        else:
            command.add_argument("--control", type=Path, required=True)
            command.add_argument("--candidate", type=Path, required=True)
            command.add_argument("--candidate-manifest", type=Path)
            command.add_argument("--edited-control", type=Path, required=True)
            command.add_argument("--case", choices=CASES, required=True)
            command.add_argument("--edited", action="store_true")
    command = modes.add_parser("phase")
    command.add_argument("request", type=Path)
    command.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "phase":
        return phase(args.root.resolve(strict=True), json.loads(args.request.read_bytes()), args.output)
    if args.mode == "measure":
        return measure(args)
    result = run_phase(args, args.output, "Author", {"operation": "author", "template": str(args.template.resolve(strict=True))})
    print(json.dumps({"passed": result["passed"], "error": result.get("error"), "output": str(args.output)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
