import argparse
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import re
from shutil import copyfile
from time import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorImportedBody import CHECK_BODY, ImportedBodyAuthor, SOLID, box_expectation
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from RunImportedBodySources import DISCLOSED, VERSION, oracle_identity


SCHEMA = "kit.sw2026.local-kernel-restore.v1"
BODY_ARRAY_LIMIT = 4096


def expected_box():
    box = box_expectation(DISCLOSED)
    return {"corners_m": box["corners"], "edges": len(box["edges"]), "faces": len(box["faces"]),
            "com_m": box["com"], "volume_m3": box["volume"], "area_m2": box["area"]}


def checked(path, checksum):
    require(re.fullmatch(r"[0-9a-f]{64}", checksum) is not None and digest(path) == checksum,
            f"packet input changed: {path.name}")
    return path


def verify_job(path, checksum, extra_tools):
    require(os.name == "nt", "run the kernel observation in the Windows guest")
    job = json.loads(checked(path, checksum).read_bytes())
    require(job["schema"] == SCHEMA and job["executable_sha256"] == ORACLE
            and job["file_version"] == VERSION and re.fullmatch(r"[0-9a-f]{40}", job["tool_revision"]),
            "kernel restore job identity differs")
    valid_bindings = ("exchange",) if extra_tools else ("dynamic", "typed_unknown")
    require(job["restore_binding"] in valid_bindings, "invalid native restoration path")
    destination = Path(job["guest_directory"])
    require(destination.parent == Path("C:\\") and re.fullmatch(r"KitKernelRestore[0-9]{2}", destination.name),
            "use a fresh guest-local kernel observation directory")
    tools = path.parent / "Tools"
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == {
        "AuthorCurves.py", "AuthorImportedBody.py", "AuthorRectangleAnchors.py", "InspectFresh.py",
        "ObserveKernelBodyRestore.py", "OracleIdentity.py", "RunImportedBodySources.py", "Swapp.py",
        *extra_tools,
    }, "use the complete measured oracle source")
    for name, expected in job["tools_sha256"].items():
        checked(tools / name, expected)
    checked(path.parent / "Control.SLDPRT", CONTROL)
    cases = job["cases"]
    require(type(cases) is dict and len(cases) <= 6, "kernel observation batch exceeds the measured process bound")
    for name, case in cases.items():
        require(re.fullmatch(r"[A-Z][A-Za-z0-9]{0,20}", name) and name not in ("Before", "After"),
                "use a distinct kernel case name")
        candidate = path.parent / (name + ".x_b")
        require(0 < candidate.stat().st_size <= 64 * 1024**2, "candidate has an unsupported stream extent")
        checked(candidate, case["sha256"])
        require(case["role"] in ("native_archive_control", "generated_disclosed"), "unknown kernel observation role")
        corners = case["expected"]["corners_m"]
        require(3 <= len(corners) < BODY_ARRAY_LIMIT and all(len(q) == 3 and all(map(isfinite, q)) for q in corners),
                "candidate needs a finite independent expected corner inventory")
        require(len(case["expected"]["com_m"]) == 3 and all(map(isfinite, case["expected"]["com_m"]))
                and all(isfinite(case["expected"][key]) and case["expected"][key] > 0 for key in ("volume_m3", "area_m2"))
                and all(type(case["expected"][key]) is int and 0 < case["expected"][key] < BODY_ARRAY_LIMIT
                        for key in ("edges", "faces")), "candidate needs independent solid mass and topology")
    return job, destination


def measure_body(observer, body, expected, *, temporary):
    require(int(observer.get(body, "GetType")) == SOLID and bool(observer.get(body, "IsTemporaryBody")) is temporary,
            "kernel result is not the expected solid")
    vertices = tuple(observer.get(body, "GetVertices") or ())
    edges = tuple(observer.get(body, "GetEdges") or ())
    faces = tuple(observer.get(body, "GetFaces") or ())
    require((len(vertices), len(edges), len(faces)) == (len(expected["corners_m"]), expected["edges"], expected["faces"]),
            "kernel result topology differs")
    points = []
    for vertex in vertices:
        vertex = observer.typed(vertex, "Vertex")
        points.append(tuple(float(q) for q in observer.get(vertex, "GetPoint")))
    remaining = list(points)
    for target in expected["corners_m"]:
        matches = [point for point in remaining if all(abs(actual - wanted) <= 1e-10
                                                       for actual, wanted in zip(point, target, strict=True))]
        require(len(matches) == 1, "kernel corner does not match the independent input")
        remaining.remove(matches[0])
        for actual, wanted in zip(matches[0], target, strict=True):
            observer.rec.close_number("vertex coordinate", actual, wanted, absolute=1e-10)
    for edge in edges:
        edge = observer.typed(edge, "Edge")
        curve = observer.typed(observer.get(edge, "GetCurve"), "Curve")
        require(bool(observer.get(curve, "IsLine")), "candidate has an unexpected nonline edge")
    for face in faces:
        face = observer.typed(face, "Face2")
        surface = observer.typed(observer.get(face, "GetSurface"), "Surface")
        require(bool(observer.get(surface, "IsPlane")) and int(observer.get(face, "GetLoopCount")) == 1,
                "candidate has an unexpected face surface or loop")
    mass = tuple(float(q) for q in observer.get(body, "GetMassProperties", 1.0))
    require(len(mass) == 12, "temporary solid mass properties are unavailable")
    for actual, wanted in zip(mass[:3], expected["com_m"], strict=True):
        observer.rec.close_number("centre coordinate", actual, wanted, absolute=1e-11)
    observer.rec.close_number("solid volume", mass[3], expected["volume_m3"], absolute=1e-22)
    observer.rec.close_number("solid area", mass[4], expected["area_m2"], absolute=1e-18)
    return {"vertices": len(vertices), "edges": len(edges), "faces": len(faces), "com_m": mass[:3],
            "volume_m3": mass[3], "area_m2": mass[4]}


def prepare_stream(observer, modeler, candidate):
    stream = observer.sw.pythoncom.CreateStreamOnHGlobal()
    if candidate is None:
        values = (*DISCLOSED["face_center_m"], 0.0, 0.0, 1.0, *DISCLOSED["size_m"])
        request = observer.sw.VARIANT(observer.sw.pythoncom.VT_ARRAY | observer.sw.pythoncom.VT_R8, values)
        seed = observer.typed(observer.get(modeler, "CreateBodyFromBox3", request), "Body2")
        measure_body(observer, seed, expected_box(), temporary=True)
        observer.get(seed, "Save", stream)
    else:
        stream.Write(candidate)
    size = int(stream.Seek(0, 2))
    require(0 < size <= 64 * 1024**2, "kernel body stream has an invalid extent")
    stream.Seek(0, 0)
    raw = stream.Read(size)
    require(len(raw) == size and (candidate is None or raw == candidate), "kernel stream input changed")
    stream.Seek(0, 0)
    return stream, raw


def phase(directory, label, expected, candidate, binding):
    import Swapp
    from OracleIdentity import application_identity

    rec = Recorder(directory / (label + ".json"), {"case": label})
    result, controller, observer = {"passed": False}, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call("launch kernel restore oracle", Swapp.Sw)
            require(controller.revision == "34.5.2", "unexpected kernel restore oracle revision")
            result["oracle_identity"] = oracle_identity(rec.call("bind restore oracle", application_identity, controller.app))
            observer = ImportedBodyAuthor(controller.app, rec, Swapp)
            modeler = observer.typed(observer.get(controller.app, "GetModeler"), "Modeler")
            stream, raw = prepare_stream(observer, modeler, candidate)
            result["payload"] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            if binding == "typed_unknown":
                interface = stream.QueryInterface(Swapp.pythoncom.IID_IUnknown)
                body = rec.call("typed IModeler.Restore(IUnknown)", modeler.Restore, interface)
            else:
                body = observer.get(modeler, "Restore", stream)
            require(body is not None, "IModeler.Restore returned no body")
            body = observer.typed(body, "Body2")
            result["restored"] = measure_body(observer, body, expected, temporary=True)
            observer.model = rec.call("create fresh native part for restored body", controller.new_part)
            part = observer.typed(observer.model, "PartDoc")
            require(not observer.get(part, "GetBodies2", SOLID, False), "native control template contains a solid")
            feature = observer.get(part, "CreateFeatureFromBody3", body, False, CHECK_BODY)
            require(feature is not None, "native part did not attach the restored body")
            feature = observer.typed(feature, "Feature")
            require(str(observer.get(feature, "GetTypeName2")) == "BaseBody", "restored body uses an unexpected owner")
            observer.rebuild()
            require(int(observer.get(observer.get(observer.model, "Extension"), "GetWhatsWrongCount")) == 0,
                    "restored body gives native rebuild diagnostics")
            retained, = observer.get(part, "GetBodies2", SOLID, False)
            result["attached"] = measure_body(observer, observer.typed(retained, "Body2"), expected, temporary=False)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and observer.model is not None:
                        controller.close_doc(observer.model)
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    result["passed"] = bool(result["passed"] and not dialogs.log and not result.get("controller_diagnostics")
                            and not rec.data["first_failure"] and not rec.data["cleanup_errors"])
    result["numeric_checks"] = len(rec.data["checks"])
    result["first_failure"] = rec.data["first_failure"]
    rec.data.update(result=result, passed=result["passed"], finished_at=time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def run(path, checksum, *, native_phase=phase, extra_tools=()):
    job, directory = verify_job(path, checksum, extra_tools)
    public = path.parent / "Result.json"
    require(not public.exists(), "kernel observation receipt already exists")
    directory.mkdir()
    pristine = directory / "Control.SLDPRT"
    copyfile(path.parent / pristine.name, pristine)
    checked(pristine, CONTROL)
    receipt = {"schema": SCHEMA, "job_sha256": checksum, "tool_revision": job["tool_revision"], "oracle_file_version": VERSION,
               "oracle_sha256": ORACLE, "restore_binding": job["restore_binding"],
               "passed": False, "phases": [], "native_writer_outputs": 0}

    def record(name, role, method, *args):
        receipt["stage"] = name
        write_json(public, receipt)
        try:
            result = method(*args)
        except Exception as error:
            print(repr(error))
            result = {"passed": False, "first_failure": type(error).__name__}
        receipt["phases"].append({"name": name, "role": role, **result})
        write_json(public, receipt)
        return result["passed"]

    with (directory / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        binding = job["restore_binding"]
        initial_app = record("ApplicationBefore", "native_application_control", control, directory, "ApplicationBefore", pristine)
        initial_body = initial_app and record("Before", "native_stream_control", native_phase, directory, "Before", expected_box(), None, binding)
        try:
            if initial_body:
                for name, case in job["cases"].items():
                    raw = checked(path.parent / (name + ".x_b"), case["sha256"]).read_bytes()
                    record(name, case["role"], native_phase, directory, name, case["expected"], raw, binding)
        except Exception as error:
            receipt["input_error"] = type(error).__name__
            print(repr(error))
        finally:
            final_body = record("After", "native_stream_control", native_phase, directory, "After", expected_box(), None, binding)
            final_app = record("ApplicationAfter", "native_application_control", control, directory, "ApplicationAfter", pristine)
    identities = [entry.get("oracle_identity") or {} for entry in receipt["phases"]]
    unique = {(item.get("process_id"), item.get("process_creation_filetime")) for item in identities}
    receipt["distinct_exact_processes"] = len(unique - {(None, None)})
    receipt["controls_healthy"] = initial_app and bool(initial_body) and final_body and final_app
    receipt["passed"] = (receipt["controls_healthy"] and receipt["distinct_exact_processes"] == len(job["cases"]) + 4
                         and all(entry["passed"] for entry in receipt["phases"]))
    receipt["stage"] = "passed" if receipt["passed"] else "failed"
    verify_job(path, checksum, extra_tools)
    write_json(public, receipt)
    print(json.dumps({name: receipt[name] for name in ("stage", "passed", "controls_healthy", "distinct_exact_processes")}))
    return 0 if receipt["passed"] else 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Observe temporary kernel bodies in SOLIDWORKS 2026")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.job.resolve(), args.job_sha256))
