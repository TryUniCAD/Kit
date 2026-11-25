from argparse import ArgumentParser
from functools import partial
import json
from pathlib import Path
import subprocess
import sys
import traceback


REFERENCE = ((-.011, -.004), (.006, -.013), (.021, -.003), (.018, .015), (-.004, .020))
PROFILE = ((-.011, -.004), (.004, -.015), (.021, -.003), (.018, .015), (-.004, .020))
DEPTH = .013371
OTHER_DEPTH = .021463
PROPERTY = ("A12bProbe", "only this authored literal should differ")
CONTRASTS = (
    ("NoOpBefore", REFERENCE, DEPTH, None),
    ("NoOpAfter", REFERENCE, DEPTH, None),
    ("CustomText", REFERENCE, DEPTH, PROPERTY),
    ("ProfileContrast", PROFILE, DEPTH, None),
    ("DepthContrast", REFERENCE, OTHER_DEPTH, None),
)


def original(root):
    sys.path.insert(0, str(root / "re/tooling/sw2026"))
    import ObserveEncoderRoundTrip

    return ObserveEncoderRoundTrip


def digest(path):
    from hashlib import sha256

    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def read_json(path):
    return json.loads(path.read_bytes())


def demand(condition, detail):
    if not condition:
        raise ValueError(detail)


def nested_features(document, member):
    def row(feature, parent, count):
        demand(len(count) < 256, "feature traversal exceeded 256 rows")
        name = str(feature.Name)
        count.append({
            "name": name, "type": str(member(feature, "GetTypeName2")),
            "id": int(member(feature, "GetID")), "parent": parent,
        })
        child = member(feature, "GetFirstSubFeature")
        while child is not None:
            row(child, name, count)
            child = member(child, "GetNextSubFeature")

    result = []
    feature = member(document, "FirstFeature")
    while feature is not None:
        row(feature, None, result)
        feature = member(feature, "GetNextFeature")
    return result


def document_properties(document, member):
    import pythoncom
    from win32com.client import VARIANT

    manager = document.Extension.CustomPropertyManager("")
    names = member(manager, "GetNames") or ()
    result = {}
    for name in names:
        literal, resolved, was_resolved, linked = (
            VARIANT(pythoncom.VT_BYREF | kind, value)
            for kind, value in ((pythoncom.VT_BSTR, ""), (pythoncom.VT_BSTR, ""),
                                (pythoncom.VT_BOOL, False), (pythoncom.VT_BOOL, False))
        )
        status = manager.Get6(name, False, literal, resolved, was_resolved, linked)
        result[name] = {
            "literal": literal.value, "resolved": resolved.value,
            "was_resolved": was_resolved.value, "linked": linked.value, "status": int(status),
        }
    return result


def observe_part(base, document):
    return {
        **base.inspect(document),
        "nested_features": nested_features(document, base.member),
        "document_properties": document_properties(document, base.member),
        "bounds_m": tuple(document.GetPartBox(True)),
    }


def save_current(base, document):
    base.member(document, "SetSaveFlag")
    errors, warnings = base.statuses()
    saved = document.Save3(1, errors, warnings)
    demand(saved and errors.value == warnings.value == 0,
           f"SOLIDWORKS Save3 failed: {saved}, {errors.value}, {warnings.value}")
    return {"saved": True, "errors": errors.value, "warnings": warnings.value}


def record_capture(base, doc, samples, folder, name, points, depth, property_value, args, working, status):
    observation = observe_part(base, doc)
    verify_part(base, observation, points, depth, property_value)
    copied = folder / name / working.name
    copied.parent.mkdir()
    with copied.open("xb") as target:
        target.write(working.read_bytes())
    samples[name] = {
        "file": f"{name}/{copied.name}", "sha256": digest(copied),
        "bytes": copied.stat().st_size, "profile_m": points, "depth_m": depth,
        "expected_document_property": property_value,
        "feature_extrusion3_args": args, "save_status": status,
        "api_observation": observation,
    }


def verify_part(base, observation, points, depth, property_value):
    base.compare_observation(observation, points, depth)
    actual = {name: row["literal"] for name, row in observation["document_properties"].items()}
    expected = {} if property_value is None else {property_value[0]: property_value[1]}
    demand(actual == expected, f"document custom property readback differs: {actual!r}")


def create_document(base, app, template, working, points, depth, observe):
    document = app.NewDocument(str(template), 0, 0.0, 0.0)
    demand(document is not None, "unable to create owned template part")
    try:
        plane = document.FeatureByName("Front Plane")
        demand(plane is not None and plane.Select2(False, 0), "Front Plane selection failed")
        manager = document.SketchManager
        manager.InsertSketch(True)
        manager.AddToDB = True
        try:
            for start, end in zip(points, (*points[1:], points[0]), strict=True):
                demand(manager.CreateLine(*start, 0, *end, 0) is not None, "profile line creation failed")
        finally:
            manager.AddToDB = False
        manager.InsertSketch(True)
        document.ClearSelection2(True)
        sketch = document.FeatureByName("Sketch1")
        demand(sketch is not None and sketch.Select2(False, 0), "profile selection failed")
        args = (
            True, False, False, 0, 0, depth, 0.0, False, False, False, False,
            0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False,
        )
        boss = document.FeatureManager.FeatureExtrusion3(*args)
        demand(boss is not None, "blind boss creation failed")
        boss.Name = "Boss-Extrude1"
        demand(document.ForceRebuild3(False), "native feature failed to rebuild")
        working.parent.mkdir(parents=True)
        observe(document, args, working, base.save(document, working))
    finally:
        app.QuitDoc(str(base.member(document, "GetTitle")))


def author_cases(base, app, request, folder, result):
    template = Path(request["template"])
    result["template_sha256"] = digest(template)
    samples = result["samples"] = {}
    workspace = folder / "Working"
    if request["operation"] == "seal":
        spec = request["spec"]
        points, depth = tuple(map(tuple, spec["profile_m"])), spec["depth_m"]
        observed = partial(record_capture, base, samples=samples, folder=folder, name="HeldOut",
                           points=points, depth=depth, property_value=None)

        def capture(doc, args, working, status):
            observed(doc, args=args, working=working, status=status)

        create_document(base, app, template, workspace / "HeldOut/Prism.SLDPRT", points, depth, capture)
        return

    def mutate(document, args, working, status):
        result["initial_save_status"] = status
        record_capture(base, document, samples, folder, "NoOpBefore", REFERENCE, DEPTH, None,
                       args, working, save_current(base, document))
        record_capture(base, document, samples, folder, "NoOpAfter", REFERENCE, DEPTH, None,
                       args, working, save_current(base, document))
        manager = document.Extension.CustomPropertyManager("")
        added = manager.Add3(PROPERTY[0], 30, PROPERTY[1], 0)
        demand(added == 0, f"adding the single literal custom property failed: {added}")
        record_capture(base, document, samples, folder, "CustomText", REFERENCE, DEPTH, PROPERTY,
                       args, working, save_current(base, document))

    create_document(base, app, template, workspace / "SingleFactor/Prism.SLDPRT", REFERENCE, DEPTH, mutate)
    for name, points, depth, text in CONTRASTS[3:]:
        def capture(doc, args, working, _):
            record_capture(base, doc, samples, folder, name, points, depth, text,
                           args, working, save_current(base, doc))
        create_document(base, app, template, workspace / name / "Prism.SLDPRT", points, depth, capture)


def inspect_saved(base, app, request, observation, *, observe=observe_part, open_options=1):
    source = Path(request["path"]).resolve(strict=True)
    original_digest = digest(source)
    demand(original_digest == request["sha256"], "native input changed before open")
    errors, warnings = base.statuses()
    document = app.OpenDoc6(str(source), 1, open_options, "", errors, warnings)
    observation.update(open_errors=errors.value, open_warnings=warnings.value)
    demand(document is not None, f"SOLIDWORKS did not open the saved part: {errors.value}")
    try:
        demand(errors.value == warnings.value == 0, "SOLIDWORKS returned load errors or warnings")
        observation["initial"] = observe(base, document)
        demand(document.ForceRebuild3(False), "native document failed to rebuild")
        observation["rebuilt"] = observe(base, document)
        points = tuple(map(tuple, request["profile_m"]))
        for state in ("initial", "rebuilt"):
            verify_part(base, observation[state], points, request["depth_m"], request["property"])
    finally:
        app.QuitDoc(str(base.member(document, "GetTitle")))
    demand(digest(source) == original_digest, "native input changed during observation")


def phase(root, request, output, *, inspect=inspect_saved):
    import pythoncom
    import win32api
    from win32com.client import DispatchEx

    base = original(root)
    sys.path.insert(0, str(root / "re/automation/ApplicationWorkers"))
    from SolidWorksAvailability import HoldMutex, IsSolidWorksRunning, OracleMutex
    from WindowsIdentity import process_start
    from WindowsProcessExit import observe_exit, watch_peer

    result = {"role": request["role"], "passed": False}
    binary = Path(request["executable"]).resolve(strict=True)
    try:
        demand(digest(binary) == request["executable_sha256"], "oracle executable digest differs")
        version = win32api.GetFileVersionInfo(str(binary), "\\")
        high, low = version["FileVersionMS"], version["FileVersionLS"]
        build = f"{high >> 16}.{high & 65535}.{low >> 16}.{low & 65535:04}"
        with HoldMutex(OracleMutex) as held:
            demand(held and not IsSolidWorksRunning(), "oracle leased or SOLIDWORKS already running")
            pythoncom.CoInitialize()
            try:
                app = DispatchEx("SldWorks.Application")
                pid = int(base.member(app, "GetProcessID"))
                peer = {"pid": pid, "started": process_start(pid)}
                with watch_peer(peer, binary) as watch:
                    demand(not base.member(app, "GetDocumentCount"), "new native process contains a document")
                    result["oracle_identity"] = {
                        **peer, "build": build, "revision": str(base.member(app, "RevisionNumber")),
                        "sha256": request["executable_sha256"],
                    }
                    try:
                        app.UserControlBackground = True
                        demand(app.UserControlBackground, "could not retain owned background session")
                        if request["operation"] in ("author", "seal"):
                            author_cases(base, app, request, output.parent, result)
                        else:
                            inspect(base, app, request, result)
                    finally:
                        if not base.member(app, "GetDocumentCount"):
                            app.ExitApp()
                            del app
                            result["exit"] = observe_exit(watch, 30000)
                        else:
                            result["cleanup_error"] = "owned process retained a document"
                demand(result.get("exit") and result["exit"]["exit_code"] == 0, "normal owned exit was not observed")
            finally:
                pythoncom.CoUninitialize()
        result["passed"] = True
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
        traceback.print_exc()
    write_json(output, result)
    return 0 if result["passed"] else 1


def supervise(args):
    output = args.output.resolve()
    output.mkdir()
    root = args.root.resolve(strict=True)
    template = str(args.template.resolve(strict=True))
    controls = args.control.resolve(strict=True)
    control_data = read_json(controls.parent / "Record.json")["authored"][controls.name]
    control = {
        "operation": "measure", "path": str(controls), "sha256": control_data["sha256"],
        "profile_m": control_data["profile_m"], "depth_m": control_data["depth_m"], "property": None,
    }
    tool = Path(__file__).resolve()
    phases = {}

    def run(label, request):
        folder = output / label
        folder.mkdir()
        target = folder / "Record.json"
        request_file = folder / "Request.json"
        write_json(request_file, {
            **request, "role": label, "executable": str(args.executable.resolve(strict=True)),
            "executable_sha256": args.executable_sha256,
        })
        with (folder / "Worker.log").open("xb") as log:
            try:
                worker = subprocess.run(
                    [sys.executable, "-B", str(tool), "--root", str(root), "phase", str(request_file), str(target)],
                    stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False,
                )
            except subprocess.TimeoutExpired:
                phases[label] = {"passed": False, "error": "owned worker exceeded 180 seconds"}
                return phases[label]
        if target.is_file():
            phases[label] = {**read_json(target), "worker_exit_code": worker.returncode,
                             "record_sha256": digest(target), "request_sha256": digest(request_file)}
        else:
            phases[label] = {"passed": False, "error": "owned worker issued no result",
                             "worker_exit_code": worker.returncode}
        return phases[label]

    before = run("ControlBefore", control)
    author = None
    if before["passed"]:
        request = {"operation": "author", "template": template}
        if args.seal_spec:
            request.update(operation="seal", spec=read_json(args.seal_spec))
        author = run("Author", request)
        if author["passed"]:
            for name, capture in author["samples"].items():
                run(name, {
                    "operation": "measure", "path": str(output / "Author" / capture["file"]),
                    "sha256": capture["sha256"], "profile_m": capture["profile_m"],
                    "depth_m": capture["depth_m"], "property": capture["expected_document_property"],
                })
    trailing = run("ControlAfter", control)
    births = {(row["oracle_identity"]["pid"], row["oracle_identity"]["started"])
              for row in phases.values() if "oracle_identity" in row}
    expected = 4 if args.seal_spec else 8
    passed = len(births) == len(phases) == expected and all(row["passed"] for row in phases.values())
    result = {
        "schema": "kit.sw2026.vendor-boss-corpus.v1", "passed": passed,
        "controls_healthy": before["passed"] and trailing["passed"],
        "split": "held-out" if args.seal_spec else "discovery", "distinct_native_processes": len(births),
        "method_sha256": digest(tool), "source_observer_sha256": digest(root / "re/tooling/sw2026/ObserveEncoderRoundTrip.py"),
        "phases": phases,
    }
    write_json(output / "Result.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "phases"}))
    return 0 if passed else 1


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    modes = parser.add_subparsers(dest="mode", required=True)
    batch = modes.add_parser("capture")
    for arg in ("output", "control", "template", "executable"):
        batch.add_argument("--" + arg, type=Path, required=True)
    batch.add_argument("--executable-sha256", required=True)
    batch.add_argument("--seal-spec", type=Path)
    child = modes.add_parser("phase")
    child.add_argument("request", type=Path)
    child.add_argument("output", type=Path)
    options = parser.parse_args()
    if options.mode == "phase":
        raise SystemExit(phase(options.root, read_json(options.request), options.output))
    raise SystemExit(supervise(options))
