from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import json
import os
import re
import sys
import time

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from HoleWizardPlan import API_SHA, APP_HASH, BASE, BUILD, CONTROL_PATH, CONTROL_SHA
from HoleWizardPlan import checked, digest, installation, packet_model, require
from ReadHoleApi import capture, encode

SCHEMA = "kit.sw2026.disclosed-hole-wizard-source.v1"
TOOLS = ("ReadHoleApi.py", "HoleWizardPlan.py", "AuthorHoleWizard.py", HERE.name)
SHARED = ("AuthorCurves.py", "AuthorAssemblySources.py", "InspectFresh.py", "InspectCircleSketch.py",
          "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py", "NestedAssemblySourcePlan.py",
          "AuthorNestedAssemblySources.py", "RunSealedNestedSourcePhase.py")
PHASES = ("Metadata", "Before", "AuthorPlainThrough", "ReopenPlainThrough",
          "AuthorCounterboreThrough", "ReopenCounterboreThrough", "After")
PRIVATE = re.compile(r"C:\\KitHoleWizardSource[0-9]{2,4}")
ARTIFACTS = {f"{state}.{suffix}" for state in ("Original", "Edited") for suffix in ("SLDPRT", "STEP", "x_t")}


def write(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def members():
    return {"InstalledHoleApi.json", "SourcePlan.json", "Control.SLDPRT",
            *(f"Tools/{name}" for name in (*TOOLS, *SHARED))}


def same_expectations(first, second):
    if isinstance(second, dict):
        return isinstance(first, dict) and first.keys() == second.keys() and all(
            same_expectations(first[key], value) for key, value in second.items())
    if isinstance(second, (tuple, list)):
        return isinstance(first, (tuple, list)) and len(first) == len(second) and all(
            same_expectations(item, wanted) for item, wanted in zip(first, second, strict=True))
    if type(second) is float:
        return type(first) is float and isclose(first, second, rel_tol=1e-14, abs_tol=1e-16)
    return type(first) is type(second) and first == second


def prepare(output, api, guest):
    require(HERE.parent.name == "hole_source" and HERE.parents[1].name == "sw2026",
            "prepare from the isolated repository checkout")
    repo = HERE.parents[4]
    require(PRIVATE.fullmatch(guest) and not output.is_relative_to(repo)
            and output.parent.is_dir() and not output.exists(), "require an unused packet and issued Windows root")
    metadata = checked(api, API_SHA)
    installation(metadata)

    def git_file(name):
        return check_output(("git", "-C", str(repo), "show", f"{BASE}:{name}"))

    control = git_file(CONTROL_PATH)
    require(digest(control) == CONTROL_SHA, "native bracket control changed")
    data = {
        **{f"Tools/{name}": HERE.with_name(name).read_bytes() for name in TOOLS},
        **{f"Tools/{name}": git_file("re/tooling/sw2026/" + name) for name in SHARED},
        "InstalledHoleApi.json": metadata, "SourcePlan.json": encode(packet_model()),
        "Control.SLDPRT": control,
    }
    require(set(data) == members(), "whole Hole Wizard packet closure is incomplete")
    output.mkdir(exist_ok=False)
    (output / "Tools").mkdir()
    for name, raw in data.items():
        write(output / name, raw)
    manifest = {"schema": SCHEMA, "base": BASE, "build": BUILD, "oracle": APP_HASH,
                "guest_private_base": guest, "phases": PHASES, "cohort": "disclosed",
                "reference_api_sha256": API_SHA, "control_sha256": CONTROL_SHA,
                "kit_writer_outputs": 0, "heldout_cases": 0,
                "files": {name: digest(raw) for name, raw in data.items()}}
    raw = encode(manifest)
    path = output / "Packet.json"
    write(path, raw)
    pin = digest(raw)
    run((sys.executable, "-E", "-B", str(output / "Tools" / HERE.name), "verify", str(path), pin),
        check=True, capture_output=True, timeout=30)
    return {"packet": str(path), "sha256": pin, "source_plan_sha256": manifest["files"]["SourcePlan.json"],
            "native_processes": 0, "heldout_inputs_read": 0}


def verify(packet, pin):
    root = packet.parent
    manifest = json.loads(checked(packet, pin))
    require(packet.name == "Packet.json" and (root / "Tools").resolve() == HERE.parent
            and (manifest["schema"], manifest["base"], manifest["build"], manifest["oracle"], manifest["cohort"])
            == (SCHEMA, BASE, BUILD, APP_HASH, "disclosed")
            and manifest["reference_api_sha256"] == API_SHA and manifest["control_sha256"] == CONTROL_SHA
            and manifest["kit_writer_outputs"] == manifest["heldout_cases"] == 0
            and manifest["phases"] == list(PHASES) and PRIVATE.fullmatch(manifest["guest_private_base"])
            and set(manifest["files"]) == members(), "foreign packet, build, tool or disclosure scope")
    inventory = tuple(root.rglob("*"))
    require(all(not item.is_symlink() for item in inventory)
            and {path.relative_to(root).as_posix() for path in inventory if path.is_file()}
            == members() | {"Packet.json"}, "unbound packet file or link")
    data = {name: checked(root / name, sha) for name, sha in manifest["files"].items()}
    installation(data["InstalledHoleApi.json"])
    require(digest(data["Control.SLDPRT"]) == CONTROL_SHA, "native bracket control does not match")
    plans = json.loads(data["SourcePlan.json"])
    require(same_expectations(plans, packet_model()), "disclosed hole arguments or independent predictions changed")
    return manifest, {job["case"]["name"]: job for job in plans["jobs"]}


def metadata_phase(output, packet):
    observed = capture()
    require(encode(observed) == (packet.parent / "InstalledHoleApi.json").read_bytes(),
            "installed HoleWizard5 type library differs from the frozen exact-build capture")
    import pythoncom

    pythoncom.CoInitialize()
    try:
        library = pythoncom.LoadRegTypeLib("{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 34, 0, 0)
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            if info.GetDocumentation(-1)[0] == "swEndConditions_e":
                enumerators = [info.GetVarDesc(row) for row in range(info.GetTypeAttr().cVars)]
                match, = (item for item in enumerators if info.GetNames(item.memid)[0] == "swEndCondThroughAll")
                require(type(match.value) is int and match.value == 1, "registered through-all enum differs")
                break
        else:
            raise ValueError("installed through-all enum has no distinct owner")
    finally:
        pythoncom.CoUninitialize()
    evidence = {"installed_api_sha256": API_SHA, "end_condition": 1, "native_processes": 0}
    write(output / "Bindings.json", encode(evidence))
    return evidence


def phase_prior(private, phase, pin):
    row = json.loads((private / phase / "Result.json").read_bytes())
    require(row["phase"] == phase and row["packet_sha256"] == pin and row["passed"] is True,
            "native prerequisite phase has no completed evidence: " + phase)
    return row


def verify_files(folder, manifest):
    require(set(manifest) == ARTIFACTS, "native and exchange artifact inventory differs")
    require(manifest["Original.SLDPRT"]["sha256"] != manifest["Edited.SLDPRT"]["sha256"],
            "independent edit did not produce a distinct saved native source")
    for name, row in manifest.items():
        content = checked(folder / name, row["sha256"])
        require(len(content) == row["bytes"] > 0 and row["status"] == [True, 0, 0],
                "native source artifact failed its original exact save lock")


def save(controller, author, folder, name):
    path = folder / name
    require(not path.exists(), "native source output has a prior owner")
    status = list(author.rec.call("save source artifact", controller.save_as, author.model, path))
    raw = path.read_bytes() if path.is_file() else b""
    require(raw and status == [True, 0, 0], "native source save failed, warned, or produced no file")
    return {"sha256": digest(raw), "bytes": len(raw), "status": status}


def control(packet, output):
    from AuthorCurves import write_json
    from InspectFresh import healthy, inspect
    from RunSealedNestedSourcePhase import opaque_identity

    path = packet.parent / "Control.SLDPRT"
    checked(path, CONTROL_SHA)
    result = {}
    inspect(path, result=result, checkpoint=lambda: write_json(output / "Native.json", result))
    require(healthy(result) and result["sha256"] == CONTROL_SHA, "native before/after control failed")
    checked(path, CONTROL_SHA)
    return {"identity": opaque_identity(result["oracle_identity"]),
            "quantity_sha256": digest(encode({name: result[name] for name in ("bodies", "mass", "features")}))}


def native_phase(job, private, output, pin, reopen):
    import Swapp
    from AuthorCurves import Recorder
    from AuthorHoleWizard import HoleAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from RunSealedNestedSourcePhase import opaque_identity

    case = job["case"]
    parent = private / ("Author" + case["name"])
    native = parent / "Native"
    snapshot_path = parent / "AuthorSnapshot.json"
    if reopen:
        previous = phase_prior(private, "Author" + case["name"], pin)
        snapshot = json.loads(checked(snapshot_path, previous["author_snapshot_sha256"]))
        require(snapshot["packet_sha256"] == pin and snapshot["case"] == case["name"],
                "previous authored artifact state belongs to another case or packet")
        files = snapshot["files"]
        verify_files(native, files)
    else:
        native.mkdir(exist_ok=False)
        files = {}
    rec = Recorder(output / "Native.json", {"case": case, "phase": "reopen" if reopen else "author", "packet_sha256": pin})
    controller = None
    states = {}
    with AssemblyLoadMonitor() as monitor:
        try:
            rec.call("verify idle exact-build oracle", Swapp.sweep)
            controller = rec.call("launch fresh native Hole Wizard source", Swapp.Sw)
            identity = rec.call("bind exact downloaded executable", application_identity, controller.app)
            require(identity["version_matches"] and controller.revision == "34.5.2", "unexpected installed source build")
            bound = opaque_identity(identity)
            author = HoleAuthor(controller.app, rec, Swapp)
            if not reopen:
                author.author(job, controller)
                require(author.get(author.model, "ForceRebuild3", False), "native author could not checkpoint its new hole")
                files["Original.SLDPRT"] = save(controller, author, native, "Original.SLDPRT")
                write(output / "NativeCheckpoint.json", encode({"file": files["Original.SLDPRT"], "qualified": False}))
            for state in ("Original", "Edited"):
                expected = job[state.casefold()]
                if reopen:
                    path = native / f"{state}.SLDPRT"
                    model, errors, warnings = rec.call("fresh read-only original or edited source", controller.open, path, read_only=True)
                    require(model is not None and errors == warnings == 0, "native source reopened with a warning or error")
                    author.model = model
                    require(Path(author.get(model, "GetPathName")).samefile(path), "native reopen selected a different file")
                    try:
                        observed = author.observe(case, expected)
                        original = snapshot["states"][state]
                        require(observed["tree"] == original["tree"] and same_expectations(observed["wizard"], original["wizard"]),
                                "reopened native tree or Wizard data differs from its saved state")
                        states[state] = observed
                    finally:
                        rec.call("close read-only native sibling", controller.close_doc, model)
                    verify_files(native, files)
                else:
                    if state == "Edited":
                        author.edit(case)
                    states[state] = author.observe(case, expected)
                    for suffix in ("SLDPRT", "STEP", "x_t"):
                        name = f"{state}.{suffix}"
                        if name not in files:
                            files[name] = save(controller, author, native, name)
                    for name, row in files.items():
                        checked(native / name, row["sha256"])
            require(states["Original"]["tree"] == states["Edited"]["tree"]
                    and states["Original"]["wizard"][case["edit_property"]] != states["Edited"]["wizard"][case["edit_property"]],
                    "live edit did not change the intended dimension under the same feature tree")
        except Exception as error:
            rec.failure(error)
            raise
        finally:
            if controller is not None:
                rec.call("close owned native source", controller.close)
                rec.data["controller_diagnostics"] = controller.diagnostics
                rec.flush()
    require(not monitor.log and not controller.diagnostics, "native source had dialogs or exit diagnostics")
    verify_files(native, files)
    if not reopen:
        write(snapshot_path, encode({"packet_sha256": pin, "case": case["name"], "files": files, "states": states}))
    rec.data.update(passed=True, dialogs=monitor.log)
    rec.flush()
    return {"identity": bound, "checks": len(rec.data["checks"]), "states": len(states),
            "author_snapshot_sha256": digest(snapshot_path.read_bytes())}


def run_phase(packet, pin, phase):
    require(os.name == "nt", "native phase runs only inside the licensed Windows oracle")
    manifest, plans = verify(packet, pin)
    from AuthorCurves import write_json
    from RunSealedNestedSourcePhase import local_trial

    private = local_trial(manifest, pin, 0, "T01")
    output = private / phase
    output.mkdir(exist_ok=False)
    row = {"phase": phase, "packet_sha256": pin, "passed": False, "started_at": time.time()}
    write_json(output / "Result.json", row)
    try:
        with (output / "Console.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
            if phase == "Metadata":
                actual = metadata_phase(output, packet)
            elif phase in ("Before", "After"):
                actual = control(packet, output)
            else:
                metadata = phase_prior(private, "Metadata", pin)
                require(metadata["installed_api_sha256"] == API_SHA, "native API authority differs")
                phase_prior(private, "Before", pin)
                require(encode(capture()) == (packet.parent / "InstalledHoleApi.json").read_bytes(),
                        "native hole API or executable changed after preflight")
                case = phase.removeprefix("Author").removeprefix("Reopen")
                actual = native_phase(plans[case], private, output, pin, phase.startswith("Reopen"))
            verify(packet, pin)
        row.update(actual, passed=True)
    except Exception as error:
        write_json(output / "Failure.json", {"type": type(error).__name__, "error": repr(error)})
        row["failure_type"] = type(error).__name__
    write_json(output / "Result.json", row | {"finished_at": time.time()})
    return {"phase": phase, "passed": row["passed"], "error_type": row.get("failure_type")}


def summary(packet, pin, output):
    require(os.name == "nt", "native summary runs only inside the licensed Windows oracle")
    manifest, plans = verify(packet, pin)
    from RunSealedNestedSourcePhase import local_trial

    private = local_trial(manifest, pin, 0, "T01")
    records = [phase_prior(private, phase, pin) for phase in PHASES]
    native = records[1:]
    require(len({row["identity"]["process_creation_filetime"] for row in native}) == 6
            and all(first["finished_at"] <= second["started_at"] for first, second in zip(records, records[1:]))
            and native[0]["quantity_sha256"] == native[-1]["quantity_sha256"],
            "source runs require six fresh lifetimes and unchanged healthy controls")
    proof = {}
    for name in plans:
        first = phase_prior(private, "Author" + name, pin)
        other = phase_prior(private, "Reopen" + name, pin)
        require(first["author_snapshot_sha256"] == other["author_snapshot_sha256"] and first["states"] == other["states"] == 2,
                "exact original and edited native source evidence differs")
        root = private / ("Author" + name)
        source = json.loads(checked(root / "AuthorSnapshot.json", first["author_snapshot_sha256"]))
        verify_files(root / "Native", source["files"])
        proof[name] = {"source_snapshot_sha256": first["author_snapshot_sha256"], "checks": first["checks"] + other["checks"],
                       "original_sha256": source["files"]["Original.SLDPRT"]["sha256"],
                       "edited_sha256": source["files"]["Edited.SLDPRT"]["sha256"]}
    record = {"schema": SCHEMA, "packet_sha256": pin, "build": BUILD, "disclosed_sources": proof,
              "native_processes": len(native), "healthy_controls": 2, "native_sources_qualified": 2,
              "heldout_cases": 0, "kit_writer_outputs": 0, "conversion_credit": 0, "passed": True}
    write(output, encode(record))
    return record


def main():
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest="action", required=True)
    builder = subs.add_parser("prepare")
    builder.add_argument("path", type=Path)
    builder.add_argument("--installed-api", required=True, type=Path)
    builder.add_argument("--guest-root", required=True)
    for mode in ("verify", "run", "summary"):
        child = subs.add_parser(mode)
        child.add_argument("path", type=Path)
        child.add_argument("sha256")
        if mode == "run":
            child.add_argument("phase", choices=PHASES)
        if mode == "summary":
            child.add_argument("output", type=Path)
    args = parser.parse_args()
    path = args.path.resolve(strict=args.action != "prepare")
    if args.action == "prepare":
        value = prepare(path, args.installed_api, args.guest_root)
    elif args.action == "verify":
        verify(path, args.sha256)
        value = {"verified": True, "native_processes": 0}
    elif args.action == "run":
        value = run_phase(path, args.sha256, args.phase)
    else:
        value = summary(path, args.sha256, args.output)
    print(json.dumps(value, sort_keys=True))
    return int(value.get("passed") is False)


if __name__ == "__main__":
    raise SystemExit(main())
