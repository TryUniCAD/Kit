from argparse import ArgumentParser
import json
import os
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile
from time import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorImportedBody import IMPORTED, SHEET, SOLID, ImportedBodyAuthor
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from ObserveKernelBodyRestore import expected_box, measure_body
from RunImportedBodySources import oracle_identity


NATIVE_CONTROL = "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325"
CASES = {"RectangularBare", "RectangularOwned", "ConcaveBare", "ConcaveOwned"}
TOOLS = {"ObserveLocalImportedPart.py", "AuthorCurves.py", "AuthorImportedBody.py", "AuthorRectangleAnchors.py",
         "RunImportedBodySources.py", "ObserveKernelBodyRestore.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"}


def snapshot(observer, expected, name, persistent, scene=None, note_names=()):
    feature = observer.get(observer.model, "FeatureByName", name)
    require(feature is not None and observer.get(feature, "GetTypeName2") == IMPORTED, "imported feature is absent")
    tree = observer.feature_tree(required_names=(name,))
    require([row["name"] for row in tree if row["type"] == IMPORTED] == [name], "expected one named imported feature")
    require(int(observer.get(observer.get(observer.model, "Extension"), "GetWhatsWrongCount")) == 0,
            "imported feature published native rebuild diagnostics")
    part = observer.typed(observer.model, "PartDoc")
    solids = tuple(observer.get(part, "GetBodies2", SOLID, False) or ())
    require(len(solids) == 1 and not observer.get(part, "GetBodies2", SHEET, False), "expected one owned solid")
    body = observer.typed(solids[0], "Body2")
    require(observer.get(body, "Name") == name, "implicit imported body label differs")
    measured = measure_body(observer, body, expected, temporary=False)
    faces = tuple(observer.get(body, "GetFaces") or ())
    feature_faces = tuple(observer.get(feature, "GetFaces") or ())
    require(len(faces) == len(feature_faces) == expected["faces"], "native import face inventories disagree")
    for value in faces:
        face = observer.typed(value, "Face2")
        observer.exact_object(observer.get(face, "GetFeature"), feature, "local body face owning feature")
        observer.exact_object(observer.get(face, "GetBody"), body, "local body face owning solid")
    token = observer.persistent_reference(feature) if persistent is None else persistent
    observer.exact_object(observer.resolve_feature(token), feature, "native persistent reference resolves to the same feature")
    extension = observer.get(observer.model, "Extension")
    state = {"needs_rebuild": int(observer.get(extension, "NeedsRebuild2")),
             "save_flag": bool(observer.get(observer.model, "GetSaveFlag")),
             "update_stamp": int(observer.get(observer.model, "GetUpdateStamp"))}
    result = {"shape": measured, "feature": name, "feature_id": int(observer.get(feature, "GetID")),
              "persistent_reference": token, "feature_faces": len(feature_faces), "application_state": state}
    if scene is not None:
        observed = tuple((row["name"], row["type"], row["parent"]) for row in tree
                         if row["type"] in ("AmbientLight", "DirectionLight"))
        require(observed == scene and any(row["type"] == "EnvFolder" and row["name"] == scene[0][2]
                                          for row in tree), "native light inventory or environment owner differs")
        result["light_tree"] = observed
    if note_names:
        note_rows = [row for row in tree if row["name"] in note_names]
        require(len(note_rows) == len(note_names) and {row["name"] for row in note_rows} == set(note_names),
                "native note tree does not contain both owned captions")
        result["note_rows"] = note_rows
        result["tree_signature"] = [(row["name"], row["type"], row["parent"], row["suppressed"]) for row in tree]
    return result


def phase(directory, label, source, source_sha, expected, feature_name, *, save=None, reference=None, scene=None, note_names=()):
    import Swapp
    from OracleIdentity import application_identity

    record = Recorder(directory / (label + ".json"), {"case": label})
    result, controller, observer = {"passed": False}, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == source_sha, "the phase input changed before open")
            record.call("verify idle oracle", Swapp.sweep)
            controller = record.call("launch exact imported-part oracle", Swapp.Sw)
            require(controller.revision == "34.5.2", "unexpected native import revision")
            result["oracle_identity"] = oracle_identity(record.call("bind oracle identity", application_identity, controller.app))
            observer = ImportedBodyAuthor(controller.app, record, Swapp)
            observer.model, error, warning = record.call("open native container", controller.open, source, read_only=save is None)
            result["open"] = {"returned_document": observer.model is not None, "error": error, "warning": warning}
            require(observer.model is not None and error == 0, "native container could not open")
            try:
                result["cold"] = snapshot(observer, expected, feature_name, reference, scene, note_names)
            except Exception as problem:
                result["cold_failure"] = repr(problem)
            observer.rebuild()
            result["rebuilt"] = snapshot(observer, expected, feature_name,
                                         result.get("cold", {}).get("persistent_reference", reference), scene, note_names)
            if save is not None and warning == 0 and "cold" in result:
                require(not save.exists(), "fresh generated save target already exists")
                status = tuple(record.call("save to a separate local file", controller.save_as, observer.model, save))
                require(status == (True, 0, 0) and save.is_file(), "generated native imported part did not save cleanly")
                result["saved_sha256"] = digest(save)
            result["passed"] = warning == 0 and "cold" in result and (save is None or "saved_sha256" in result)
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and observer.model is not None:
                        controller.close_doc(observer.model)
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    record.failure(error, cleanup=True)
    result["first_failure"] = record.data["first_failure"]
    result["numeric_checks"] = len(record.data["checks"])
    result["passed"] = result["passed"] and not dialogs.log and not record.data["cleanup_errors"] \
        and not result["first_failure"] and not result.get("controller_diagnostics") and digest(source) == source_sha
    record.data.update(result=result, finished_at=time(), passed=result["passed"])
    record.flush()
    return result | {"record_sha256": digest(record.path)}


def run(job_path, expected):
    require(os.name == "nt" and digest(job_path) == expected, "use the committed frozen job in the Windows oracle")
    job = json.loads(job_path.read_bytes())
    packet = job_path.parent
    tools = Path(__file__).resolve().parent
    require(tools == packet / "Tools" and job["schema"] == "kit.sw2026.imported-local-part-native-job.v1"
            and set(job["tools"]) == TOOLS and all(digest(tools / name) == value for name, value in job["tools"].items()),
            "native probe tools do not match the locked job")
    require(job["oracle_sha256"] == ORACLE and digest(packet / "Build.json") == job["build_sha256"], "build identity differs")
    build = json.loads((packet / "Build.json").read_bytes())
    require(build["schema"] == "kit.sw2026.generated-imported-local-part.v1" and set(build["cases"]) == CASES
            and build["runtime_input_file_reads"] == 0 and build["heldout_payloads_read"] == 0,
            "expected only the pinned model-generated discovery candidates")
    directory = Path(job["guest_root"])
    require(directory.drive.casefold() == "c:" and len(directory.parts) == 2
            and re.fullmatch(r"KitImportedProbe[0-9]{2}", directory.name) and not directory.exists(), "use a new oracle folder")
    result_path = packet / "Result.json"
    require(not result_path.exists(), "job already has a public receipt")
    directory.mkdir()
    (directory / "Candidates").mkdir()
    seed = directory / "Control.SLDPRT"
    native = directory / "ImportedControl.SLDPRT"
    for path, checksum in ((seed, CONTROL), (native, NATIVE_CONTROL)):
        copyfile(packet / path.name, path)
        require(digest(path) == checksum, "native control identity differs")
    report = {"schema": "kit.sw2026.imported-local-part-native-probe.v1", "job_sha256": expected,
              "build_sha256": job["build_sha256"], "writer_revision": job["writer_revision"],
              "oracle_file_version": "34.5.2.0604", "oracle_sha256": ORACLE, "phases": {}, "heldout_cases": 0,
              "public_writer_qualified": False, "started_at": time()}

    def record(name, function, *args, **kwargs):
        result = function(*args, **kwargs)
        report["phases"][name] = result
        write_json(result_path, report)
        print(json.dumps({"phase": name, "passed": result["passed"], "open": result.get("open"),
                          "cold_failure": result.get("cold_failure"), "failure": result.get("first_failure")}), flush=True)
        return result

    initial = record("ControlBefore", control, directory, "ControlBefore", seed)
    imported = record("ImportedControl", phase, directory, "ImportedControl", native, NATIVE_CONTROL, expected_box(), "Imported1")
    if initial["passed"] and imported["passed"]:
        for name, case in sorted(build["cases"].items()):
            path = directory / "Candidates" / (name + ".SLDPRT")
            require(PureWindowsPath(path) == PureWindowsPath(case["native_path"]), "candidate needs its own encoded guest path")
            copyfile(packet / "Candidates" / path.name, path)
            saved = directory / (name + "Saved.SLDPRT")
            row = record(name, phase, directory, name, path, case["sha256"], case["expected_si"], case["feature"], save=saved)
            if row["passed"]:
                record(name + "Reopen", phase, directory, name + "Reopen", saved, row["saved_sha256"], case["expected_si"],
                       case["feature"], reference=row["rebuilt"]["persistent_reference"])
    final = record("ControlAfter", control, directory, "ControlAfter", seed)
    phases = report["phases"]
    identities = {tuple(row["oracle_identity"][field] for field in ("process_id", "process_creation_filetime"))
                  for row in phases.values() if row.get("oracle_identity")}
    report["distinct_native_processes"] = len(identities)
    report["controls_healthy"] = bool(initial["passed"] and imported["passed"] and final["passed"] and len(identities) == len(phases))
    report["clean_lifecycles"] = sorted(name for name in CASES if report["controls_healthy"]
                                        and phases.get(name, {}).get("passed") and phases.get(name + "Reopen", {}).get("passed"))
    report["finished_at"] = time()
    write_json(result_path, report)
    return int(not report["controls_healthy"])


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure generated imported part archives on the exact native oracle")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.job.resolve(), args.job_sha256))
