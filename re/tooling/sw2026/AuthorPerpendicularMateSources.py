from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import argparse
import json
import os
from pathlib import Path
from shutil import copyfile
import time

from AuthorCurves import Recorder, digest, require, write_json
from PerpendicularApiMetadata import metadata
from PerpendicularMateEvidence import author_mate, capture, component_map, edit_live, same_file, signature
from PerpendicularSourcePlan import PARAMETERS, SCHEMA as SPEC_SCHEMA, SLOTS, disclosed_cases, expected_transforms, heldout_cases, validate


SCHEMA = "kit.sw2026.perpendicular-mate-source-phases.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
SCRIPT = Path(__file__).resolve()
TOOLS = ("AuthorPerpendicularMateSources.py", "PerpendicularSourcePlan.py", "PerpendicularApiMetadata.py", "PerpendicularMateEvidence.py",
         "PreparePerpendicularMateSources.py",
         "AuthorCurves.py", "AuthorAssemblySources.py", "AssemblyMateEvidence.py", "InspectFresh.py", "InspectCircleSketch.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py")
PHASES = ("metadata", "seal", "before", "author", "reopen-source", "reopen-edited", "after", "lock")


def checked(path, expected, owner=None):
    require(path.is_file() and not path.is_symlink() and (owner is None or path.resolve().is_relative_to(owner.resolve()))
            and digest(path) == expected, "a pinned perpendicular source input changed")
    return path


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, expected, root).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL
            and job["writer_output_count"] == 0 and job["native_acceptance"] is False and job["heldout_designs_guest_private"] is True,
            "use the source-only perpendicular packet")
    require(SCRIPT.parent == root / "Tools" and set(job["tools_sha256"]) == set(TOOLS), "use the frozen source author tools")
    for name, wanted in job["tools_sha256"].items():
        checked(root / "Tools" / name, wanted, root / "Tools")
    checked(root / "Control.SLDPRT", CONTROL, root)
    binding = json.loads(checked(root / "NativeBinding.json", job["native_binding_sha256"], root).read_bytes())
    require(binding["schema"] == "kit.sw2026.perpendicular-mate-native-source.v1" and binding["document_version"] == 19000
            and binding["native_build"] == "34.5.2.0604" and binding["native_processes_started"] == binding["heldout_inputs_read"] == 0,
            "the perpendicular native source binding differs")
    observed = json.loads(checked(root / "Disclosed.json", job["disclosed_sha256"], root).read_bytes())
    require(observed == {"schema": SPEC_SCHEMA, "cases": disclosed_cases()}, "disclosed source intent changed")
    return job


def private_root(job, expected, identifier):
    import ctypes

    root = Path(job["guest_private_base"])
    drive = ctypes.windll.kernel32.GetDriveTypeW
    drive.argtypes = (ctypes.c_wchar_p,)
    drive.restype = ctypes.c_uint
    require(root.is_absolute() and root.resolve() == root and drive(root.anchor) == 3, "source privacy requires a canonical fixed guest drive")
    result = root / expected / identifier
    result.mkdir(parents=True, exist_ok=True)
    return result


def previous(root, identifier, phase, expected):
    path = root / "Progress" / identifier / phase / "Record.json"
    row = json.loads(path.read_bytes())
    require(row["packet_sha256"] == expected and row["case_id"] == identifier and row["phase"] == phase
            and row["stage"] == "passed" and row["passed"] is True, "a native source prerequisite is incomplete")
    return row


def case_input(root, job, expected, identifier):
    if identifier.startswith("D"):
        return next(row for row in disclosed_cases() if row["id"] == identifier)
    sealed = previous(root, "D00", "seal", expected)
    base = private_root(job, expected, "D00")
    pack = json.loads(checked(base / "SealedSpecs.json", sealed["sealed_spec_sha256"], base).read_bytes())
    require(pack["schema"] == SPEC_SCHEMA and len(pack["cases"]) == 2, "the sealed perpendicular source cohort differs")
    return validate(next(row for row in pack["cases"] if row["id"] == identifier))


class SourceRecorder(Recorder):
    def __init__(self, path, job, publish):
        self.publish = publish
        self.last_public = float("-inf")
        super().__init__(path, job)

    def flush(self):
        super().flush()
        now = time.monotonic()
        if now - self.last_public >= 1:
            self.publish(progress_at=time.time())
            self.last_public = now


def identity(row):
    keys = ("process_id", "process_creation_filetime", "file_version", "sha256")
    require(row["version_matches"] and row["sha256"] == ORACLE and row["file_version"] == "34.5.2.0604"
            and type(row["process_creation_filetime"]) is int and row["process_creation_filetime"] > 0,
            "the source oracle does not match the pinned build")
    return {name: row[name] for name in keys}


def phase_paths(base, case, edited=False):
    folder = base / "Native" / ("Edited" if edited else "Source")
    return folder / (case["name"] + ".SLDASM"), folder / (case["child_name"] + ".SLDPRT")


def save_pair(author, controller, model, assembly, child, parent_path, child_path):
    from AuthorAssemblySources import save_owned_child

    parent_path.parent.mkdir(parents=True, exist_ok=False)
    child_status = list(author.rec.call("save exact owned native child", controller.save_as, child, child_path))
    require(child_status == [True, 0, 0] and same_file(author.get(child, "GetPathName"), child_path), "native child SaveAs failed or warned")
    saved_child = save_owned_child(author, assembly, child_path, 2, author.rec, parent_path.parent, basename=child_path.name)
    parent_status = list(author.rec.call("save exact owned native assembly after child", controller.save_as, model, parent_path))
    require(parent_status == [True, 0, 0] and digest(child_path) == saved_child["native_sha256"], "native parent SaveAs failed, warned or changed the synchronized child")
    return {"parent": {"status": parent_status, "sha256": digest(parent_path), "bytes": parent_path.stat().st_size},
            "child": {"status": saved_child["save_status"], "sha256": saved_child["native_sha256"], "bytes": saved_child["native_bytes"],
                      "update_stamp": saved_child["update_stamp"]}}


def assert_pairs(base, case, saved):
    require(set(saved) == {"source", "edited"}, "both ordinary native source states must remain locked")
    for key in saved:
        for role, path in zip(("parent", "child"), phase_paths(base, case, key == "edited"), strict=True):
            item = saved[key][role]
            require(item["status"] == [True, 0, 0] and checked(path, item["sha256"], base).stat().st_size == item["bytes"],
                    "an immutable native source sibling changed")


def make_sources(author, controller, case, base, seed):
    import Swapp

    base.mkdir(parents=True, exist_ok=True)
    owned = base / (case["child_name"] + ".SLDPRT")
    copyfile(seed, owned)
    checked(owned, CONTROL, base)
    child, errors, warnings = author.rec.call("open private native child author seed", controller.open, owned)
    require(child is not None and errors == warnings == 0 and same_file(author.get(child, "GetPathName"), owned), "the native child author seed failed or warned")
    for name, value in zip(PARAMETERS, case["child_size_m"], strict=True):
        parameter = author.get(child, "Parameter", name)
        require(parameter is not None and int(author.get(parameter, "SetSystemValue3", value, 1, Swapp.nothing())) == 0,
                "an independently authored source dimension was rejected")
    require(bool(author.get(child, "ForceRebuild3", False)), "the authored child did not rebuild")
    template = Path(author.rec.call("resolve registered native assembly template", controller.template, "assembly"))
    require(template.is_absolute() and template.suffix.lower() == ".asmdot" and template.is_file(), "the registered native assembly template is unavailable")
    model = author.get(controller.app, "NewDocument", str(template), 0, 0.0, 0.0)
    require(model is not None, "native assembly source creation failed")
    assembly = author.typed(model, "AssemblyDoc")
    matrices = expected_transforms(case)
    names = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_BSTR, [str(owned)] * 2)
    transforms = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, [value for row in matrices for value in row])
    origins = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_BSTR, [""] * 2)
    values = author.get(assembly, "AddComponents3", names, transforms, origins)
    require(values is not None and len(values) == 2, "native source insertion count differs")
    components = component_map(author, assembly, case, owned)
    author_mate(author, model, assembly, components, case)
    require(bool(author.get(model, "ForceRebuild3", False)), "the new native perpendicular source did not rebuild")
    initial = capture(author, model, assembly, owned, case)
    saved = {"source": save_pair(author, controller, model, assembly, child, *phase_paths(base, case))}
    source = capture(author, model, assembly, phase_paths(base, case)[1], case)
    require(signature(initial) == signature(source), "the first native source save changed feature or datum identity")
    edit_live(author, model, assembly, child, phase_paths(base, case)[1], case)
    edited = capture(author, model, assembly, phase_paths(base, case)[1], case, True)
    require(signature(source) == signature(edited), "the perpendicular live edit changed semantic ownership")
    saved["edited"] = save_pair(author, controller, model, assembly, child, *phase_paths(base, case, True))
    final = capture(author, model, assembly, phase_paths(base, case, True)[1], case, True)
    require(signature(edited) == signature(final), "the edited native source save changed ownership")
    assert_pairs(base, case, saved)
    result = {"source": source, "edited": final, "saved_files": saved,
              "template_sha256": digest(template), "active_angular_correction_proven": False,
              "valid_live_reorientation_and_depth_edit": True, "writer_output_count": 0}
    write_json(base / "SavedAuthor.json", result)
    return result


def reopen_sources(author, controller, case, base, edited, authored):
    checked(base / "SavedAuthor.json", authored["saved_author_sha256"], base)
    prior = json.loads((base / "SavedAuthor.json").read_bytes())
    assert_pairs(base, case, prior["saved_files"])
    parent_path, child_path = phase_paths(base, case, edited)
    model, errors, warnings = author.rec.call("fresh open immutable native perpendicular source", controller.open, parent_path, read_only=True)
    require(model is not None and errors == warnings == 0 and same_file(author.get(model, "GetPathName"), parent_path), "native source fresh open failed or warned")
    assembly = author.typed(model, "AssemblyDoc")
    first = capture(author, model, assembly, child_path, case, edited)
    require(bool(author.get(model, "ForceRebuild3", False)), "native source fresh rebuild failed")
    second = capture(author, model, assembly, child_path, case, edited)
    wanted = prior["edited" if edited else "source"]
    require(signature(first) == signature(second) == signature(wanted), "the native source lost its exact tree, ordered endpoint or ownership across fresh reopen")
    assert_pairs(base, case, prior["saved_files"])
    return {"initial": first, "rebuilt": second, "saved_files": prior["saved_files"], "inputs_unchanged": True}


def measure(job, case, phase, base, raw, seed, authored, publish, expected_api):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    require(metadata() == expected_api, "the registered API metadata changed since preflight")
    recorder = SourceRecorder(raw, {"case": case, "phase": phase}, publish)
    result, controller = {"passed": False}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle perpendicular source oracle", Swapp.sweep)
            controller = recorder.call("start fresh perpendicular source oracle", Swapp.Sw)
            actual = recorder.call("verify exact perpendicular source oracle", application_identity, controller.app)
            result["oracle_identity"] = identity(actual)
            publish(stage="native_source", identity=result["oracle_identity"])
            author = CurveAuthor(controller.app, recorder, Swapp)
            if phase == "author":
                result.update(make_sources(author, controller, case, base, seed))
            else:
                result.update(reopen_sources(author, controller, case, base, phase == "reopen-edited", authored))
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
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics")
                            and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    require(result["passed"], "the private native perpendicular source phase failed")
    value = {"identity": result["oracle_identity"]}
    if phase == "author":
        value.update(saved_author_sha256=digest(base / "SavedAuthor.json"), native_artifacts=public_artifacts(result["saved_files"]))
    return value


def control(seed, raw, publish):
    from InspectFresh import healthy, inspect

    result = {}
    def checkpoint():
        write_json(raw, result)
        if result.get("oracle_identity"):
            publish(identity=identity(result["oracle_identity"]), stage="native_control")
    inspect(seed, result=result, checkpoint=checkpoint)
    require(healthy(result) and identity(result["oracle_identity"]), "the bracketing native control failed")
    return {"identity": identity(result["oracle_identity"])}


def public_artifacts(saved):
    return {state: {role: {key: row[key] for key in ("sha256", "bytes")} for role, row in pair.items()}
            for state, pair in saved.items()}


def lock_case(root, job, expected, identifier):
    phases = ("before", "author", "reopen-source", "reopen-edited", "after")
    rows = [previous(root, identifier, phase, expected) for phase in phases]
    identities = [row["identity"]["process_creation_filetime"] for row in rows]
    require(len(identities) == len(set(identities)) == 5, "source locking requires five distinct fresh native processes")
    case = case_input(root, job, expected, identifier)
    base = private_root(job, expected, identifier) if identifier.startswith("H") else root / "Disclosed" / identifier
    prior = json.loads(checked(base / "SavedAuthor.json", rows[1]["saved_author_sha256"], base).read_bytes())
    assert_pairs(base, case, prior["saved_files"])
    return {"source_locked": True, "heldout_source_locked": identifier.startswith("H"),
            "native_artifacts": public_artifacts(prior["saved_files"]), "source_manifest_sha256": digest(base / "SavedAuthor.json")}


def run(args, path, job):
    require(os.name == "nt", "perpendicular source phases run only inside the Windows guest")
    identifier, phase = args.case_id, args.phase
    require((identifier == "D00" and phase in ("metadata", "seal")) or (identifier in SLOTS and phase not in ("metadata", "seal")),
            "the source phase is outside its declared slot")
    root = path.parent
    output = root / "Progress" / identifier / phase
    output.mkdir(parents=True, exist_ok=False)
    state = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "case_id": identifier, "phase": phase,
             "stage": "verifying", "passed": False, "started_at": time.time(), "writer_output_count": 0}
    allowed = {"stage", "passed", "finished_at", "progress_at", "identity", "private_record_sha256", "saved_author_sha256",
               "native_artifacts", "source_locked", "heldout_source_locked", "source_manifest_sha256", "sealed_spec_sha256", "api_metadata_sha256"}
    def publish(**changes):
        require(set(changes) <= allowed, "private source detail cannot be published")
        state.update(changes)
        write_json(output / "Record.json", state)
    publish()
    raw = None
    try:
        private = private_root(job, args.packet_sha256, identifier)
        detail = private / phase
        detail.mkdir(exist_ok=False)
        raw = detail / "Private.json"
        with (detail / "Console.log").open("w", encoding="utf-8") as stream, redirect_stdout(stream), redirect_stderr(stream):
            if phase == "metadata":
                write_json(raw, metadata())
                copyfile(raw, root / "ApiMetadata.json")
                result = {"api_metadata_sha256": digest(raw)}
            elif phase == "seal":
                previous(root, "D00", "metadata", args.packet_sha256)
                file = private / "SealedSpecs.json"
                require(not file.exists(), "sealed source specifications are immutable")
                write_json(file, {"schema": SPEC_SCHEMA, "cases": heldout_cases()})
                result = {"sealed_spec_sha256": digest(file)}
            elif phase in ("before", "after"):
                previous(root, "D00", "metadata", args.packet_sha256)
                result = control(root / "Control.SLDPRT", raw, publish)
            elif phase == "lock":
                result = lock_case(root, job, args.packet_sha256, identifier)
            else:
                meta = previous(root, "D00", "metadata", args.packet_sha256)
                previous(root, identifier, "before", args.packet_sha256)
                api = json.loads(checked(root / "ApiMetadata.json", meta["api_metadata_sha256"], root).read_bytes())
                case = case_input(root, job, args.packet_sha256, identifier)
                base = private if identifier.startswith("H") else root / "Disclosed" / identifier
                authored = None if phase == "author" else previous(root, identifier, "author", args.packet_sha256)
                result = measure(job, case, phase, base, raw, root / "Control.SLDPRT", authored, publish, api)
            if not raw.exists():
                write_json(raw, result)
            verify(path, args.packet_sha256)
        publish(**result, stage="passed", passed=True, finished_at=time.time(), private_record_sha256=digest(raw))
    except Exception as error:
        if raw is not None:
            write_json(raw.with_name("Failure.json"), {"error": repr(error)})
        publish(stage="failed", passed=False, finished_at=time.time())
    if raw is not None and identifier.startswith("D") and phase != "seal":
        disclosed = root / "Disclosed" / identifier
        disclosed.mkdir(parents=True, exist_ok=True)
        if raw.exists():
            copyfile(raw, disclosed / (phase + ".json"))
        if raw.with_name("Failure.json").exists():
            copyfile(raw.with_name("Failure.json"), disclosed / (phase + "Failure.json"))
    return {key: state[key] for key in ("case_id", "phase", "stage", "passed")}


def main():
    parser = argparse.ArgumentParser(description="Author or measure one ordinary perpendicular source phase while preserving guest-private holdouts")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--case-id", choices=("D00", *SLOTS))
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    try:
        job = verify(path, args.packet_sha256)
        if args.command == "verify":
            result = {"passed": True, "native_processes_started": 0, "heldout_inputs_read": 0}
        else:
            require(args.case_id is not None and args.phase is not None, "one source slot and phase are required")
            result = run(args, path, job)
    except Exception:
        result = {"passed": False, "stage": "preflight_failed"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
