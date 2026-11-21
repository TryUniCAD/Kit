from argparse import ArgumentParser
from ast import parse
from copy import deepcopy
from io import BytesIO
from math import pi
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import re
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
LANE = "re/tooling/sw2026/linear_pattern"
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent)]

from PatternDatumHoldoutIntent import case_design
from PatternDatumHoldoutPacket import CONTROLS, PREVIOUS_RESULT, verify as verify_source
from PatternEnvelopePacket import BUILD, ORACLE, checked, digest, encode, executable_path, require
from PlanPatternEvaluation import DRIVERS, STATES, close, compare_native, planned
from RunPatternEvaluation import COMPILER, DISCLOSED_RESULT_SHA, DISCLOSED_TRIAL_SHA, EXPECTED_PHASES, FIRST_WRITER
from RunPatternEvaluation import INTAKE_SHA, INTENT_SHA, OBSERVER, OBSERVER_SHA, PRIVATE_EVAL, PRIVATE_SOURCE
from RunPatternEvaluation import SCHEMA, SOURCE, SOURCE_LOCK_REVISION, SOURCE_SHA, TRIAL, WRITER, WRITER_TREE, verified, unpack_compiler


SOURCE_FILES = ("LocalLinearPatternDatumIntentLock01.json", "LocalLinearPatternDatumSourceLock01.json")
MEASUREMENTS = "re/solidworks/measurements/2026"
GUARD = "tests/Convert/Solidworks/Research/ConstructionGuard.py"
EVALUATION_TOOLS = ("PlanPatternEvaluation.py", "ObservePatternEvaluation.py", "RunPatternEvaluation.py")
DISCLOSED = "GeneratedLocalPatternNative02"
DISCLOSED_BUILD = "b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3"
AUDIT_SCRIPT = (
    "import json,sys; from pathlib import Path; p=Path(sys.argv[1]).resolve(); "
    "sys.path.insert(0,str(p.parent)); sys.argv=[str(p)]; "
    "import LocalPatternContainerProcess as m; m.main(); "
    "sys.stderr.write(json.dumps(m.audit.ModuleReads))"
)


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def git_text(*args):
    return git(*args).decode().strip()


def sha_row(raw):
    return {"bytes": len(raw), "sha256": digest(raw)}


def chronology(source_public, shipped):
    require(git_text("rev-parse", WRITER + ":src") == WRITER_TREE, "frozen production code changed")
    git("merge-base", "--is-ancestor", SOURCE_LOCK_REVISION, FIRST_WRITER)
    git("merge-base", "--is-ancestor", FIRST_WRITER, WRITER)
    git("merge-base", "--is-ancestor", OBSERVER, WRITER)
    git("merge-base", "--is-ancestor", WRITER, shipped)
    require(git("show", OBSERVER + ":" + LANE + "/ObserveGeneratedLinearPattern.py")
            == git("show", WRITER + ":" + LANE + "/ObserveGeneratedLinearPattern.py"), "qualified observer changed")
    expected_paths = [source_public / name for name in ("IntentLock.json", "SourceLock.json")]
    known = [checked(path, pin) for path, pin in zip(expected_paths, (INTENT_SHA, SOURCE_SHA), strict=True)]
    require(all(git("show", SOURCE_LOCK_REVISION + ":" + MEASUREMENTS + "/" + name) == raw
                for name, raw in zip(SOURCE_FILES, known, strict=True)), "published source receipt is outside the tracked lock")
    intent, source = map(json.loads, known)
    introduced = int(git_text("show", "-s", "--format=%ct", FIRST_WRITER))
    require(source["passed"] and source["complete_distinct_processes"] == 16
            and source["private_data_guest_only"] is True and source["writer_output_count"] == 0
            and intent["writer_output_count"] == intent["native_processes_started"] == 0
            and intent["sealed_at_unix_ns"] == source["sealed_at_unix_ns"] < source["finished_at_unix_ns"] < introduced * 10**9,
            "native source acceptance did not predate the first whole compiler")
    return {"source_sealed_ns": source["sealed_at_unix_ns"], "source_completed_ns": source["finished_at_unix_ns"],
            "first_writer_commit_unix_s": introduced}


def public_native(plan_folder):
    packet = plan_folder / "Packet"
    record = plan_folder / "NativeResult"
    known = json.loads(checked(packet / "Packet.json", DISCLOSED_TRIAL_SHA))
    report = json.loads(checked(record / "Result.json", DISCLOSED_RESULT_SHA))
    build = json.loads(checked(packet / "Build.json", DISCLOSED_BUILD))
    require(report["passed"] and report["build"] == BUILD and report["packet_sha256"] == DISCLOSED_TRIAL_SHA
            and report["build_sha256"] == DISCLOSED_BUILD and report["heldout_cases"] == 0
            and report["distinct_processes"] == 6 and all(row["passed"] for row in report["controls"].values())
            and len(report["phases"]) == 4 and all(row["passed"] for row in report["phases"].values()),
            "disclosed generated family did not pass its controlled native D3 lifecycles")
    require(known["files"]["Build.json"] == DISCLOSED_BUILD, "known disclosed neutral build differs")
    return build["model_cases"]


def source_snapshot(state):
    pattern = state["pattern"]
    plate, seed = state["plate_boss"], state["seed_boss"]
    return {"tree": state["tree"], "dependencies": {"PlateBoss": plate["parents"], "SeedBoss": seed["parents"],
                                                  "LinearPattern": pattern["parents"]},
            "boss_modes": [plate, seed], "datum": state["datum"],
            "profiles": [state["plate_profile"], state["seed_profile"]],
            "pattern_mode": {"FeatureScope": pattern["values"]["FeatureScope"], "AutoSelect": pattern["values"]["AutoSelect"],
                             "scoped_bodies": pattern["feature_scope_body_count"]},
            "pattern": {"parents": pattern["parents"], "drivers": {"D1": pattern["values"]["D1TotalInstances"],
                                                                  "D3": pattern["values"]["D1Spacing"]}},
            "driver_owners": {"LinearPattern": [row["full_name"].split("@")[:2] for row in pattern["dimensions"]["all"]]},
            "geometry": {"body_count": state["bodies"], "mass": state["mass"], "bounds_m": state["bounds"]["minmax"],
                         "vertices_m": state["bounds"]["vertices"], "face_count": state["bounds"]["faces"],
                         "rebuild_diagnostics": 0, "feature_diagnostics": []}}


def smoke_comparator(folder):
    controls = json.loads(checked(folder / "Result.json", PREVIOUS_RESULT))
    require(controls["native_lifecycle_passed"] and controls["distinct_processes"] == 6
            and len(controls["phases"]) == 4 and all(row["passed"] for row in controls["controls"].values()),
            "disclosed source lifecycles need their own healthy bracket")
    stages = {}
    for phase in controls["phases"]:
        case, operation = phase["case"], phase["phase"]
        data = json.loads(checked(folder / case / operation / "Record.json", phase["sha256"]))
        require(data["passed"] and data["source_immutable"] and not data["dialogs"]
                and data["checks"] and all(check["passed"] for check in data["checks"]),
                "disclosed source phase lacks exact numerical or lifecycle evidence")
        stages.setdefault(case, {})[operation] = source_snapshot(data["authored" if operation == "author" else "reopened"])
    require(set(stages) == {"Short", "Tall"}, "disclosed source smoke lacks its two prior geometries")
    for rows in stages.values():
        require(len(rows["author"]["tree"]) == 30, "disclosed ordinary recursive tree differs")
        compare_native(rows["author"], rows["pristine-reopen"])
    actual = stages["Short"]["pristine-reopen"]
    malformed = deepcopy(actual)
    malformed["dependencies"]["LinearPattern"].insert(0, "PlateBoss")
    changed = deepcopy(actual)
    changed["geometry"]["vertices_m"][0][0] += 0.001
    for altered, expected in ((malformed, "native scope, tree owner, or driving dimension differs at dependencies"),
                              (changed, "missing or ambiguous physical vertex or sketch point")):
        try:
            compare_native(altered, actual)
        except ValueError as error:
            require(str(error) == expected, "disclosed negative reached a different comparison")
        else:
            raise ValueError("disclosed malformed owner or physical point passed")
    return {"source_result_sha256": PREVIOUS_RESULT, "matching_disclosed_phase_pairs": 2,
            "recursive_rows_per_pair": 30, "refused_dependency_and_vertex_contrasts": 2}


def relevant_sources():
    listing = git("ls-tree", "-r", "-z", WRITER, "src", "re/tooling/sw2026", GUARD)
    inventory = {}
    for line in listing.decode().strip("\0").split("\0"):
        metadata, name = line.split("\t", maxsplit=1)
        mode, kind, blob = metadata.split(" ")
        if name.endswith(".py"):
            require(kind == "blob" and mode in ("100644", "100755"), "compiler closure contains a source link")
            inventory[name] = blob
    listing = "\n".join(inventory.values()) + "\n"
    result = run(("git", "cat-file", "--batch"), cwd=ROOT, input=listing.encode(),
                 capture_output=True, check=True)
    source = {}
    stream = BytesIO(result.stdout)
    for name, expected in inventory.items():
        blob, kind, length = stream.readline().decode().split()
        require(blob == expected and kind == "blob", "frozen source blob identity differs")
        source[name] = stream.read(int(length))
        require(len(source[name]) == int(length) and stream.read(1) == b"\n", "incomplete frozen source blob")
    require(not stream.read() and not result.stderr, "unexpected frozen source output")
    for directory in ("tests", "tests/Convert", "tests/Convert/Solidworks", "tests/Convert/Solidworks/Research"):
        path = directory + "/__init__.py"
        if git_text("ls-tree", WRITER, path):
            source[path] = git("show", WRITER + ":" + path)
    require(COMPILER in source and GUARD in source, "compiler owner or its runtime input guard is missing")
    return source


def write_sources(files, root):
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as target:
            target.write(data)


def trace_compiler(python, workspace, disclosed, files):
    write_sources(files, workspace)
    discovered = {COMPILER, GUARD, *[name for name in files if name.startswith("tests/") and name.endswith("/__init__.py")]}
    manifest = {}
    for case, rows in disclosed.items():
        original = rows["original"]
        argv = [str(python), "-I", "-B", "-c", AUDIT_SCRIPT, str(workspace / COMPILER)]
        observed = run(argv, input=encode(original["modeled_input"]), cwd=workspace, capture_output=True, timeout=60, check=False)
        require(observed.returncode == 0, "Python 3.12 compiler closure discovery failed\n" + observed.stderr.decode())
        proof = json.loads(observed.stdout)
        require(proof["native_container"] == original["native_container"] and proof["guarded_runtime_reads"] == 0,
                "disclosed proof compiler bytes differ from their accepted native source")
        paths = set()
        for name in json.loads(observed.stderr):
            local = Path(name).resolve()
            if local.is_file() and local.is_relative_to(workspace):
                paths.add(local.relative_to(workspace).as_posix())
        require(COMPILER not in paths and paths <= files.keys(), "untracked import escaped source closure discovery")
        discovered.update(paths)
        manifest[case] = {"guarded_runtime_reads": 0, "generated_container": proof["native_container"]}
    return {name: files[name] for name in sorted(discovered)}, manifest


def source_archive(files):
    saved = BytesIO()
    with ZipFile(saved, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in files.items():
            parse(data, filename=name, feature_version=(3, 12))
            info = ZipInfo(name)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    return saved.getvalue()


def smoke_compiler(python, workspace, disclosed, proof):
    for case, rows in disclosed.items():
        original = rows["original"]
        model = encode(original["modeled_input"])
        for binary in (False, True):
            argv = [str(python), "-I", "-B", str(workspace / COMPILER), *(["--binary"] if binary else [])]
            result = run(argv, input=model, cwd=workspace, capture_output=True, timeout=60, check=False)
            require(result.returncode == 0 and not result.stderr, "frozen closed Python 3.12 compiler refused\n" + result.stderr.decode())
            if binary:
                require(sha_row(result.stdout) == {key: original["native_container"][key] for key in ("bytes", "sha256")},
                        "frozen transport bytes differ from the disclosed qualified compiler")
            else:
                row = json.loads(result.stdout)
                require(row["guarded_runtime_reads"] == 0 and row["native_container"] == original["native_container"],
                        "closed compiler emitted a different independent proof")
        proof[case]["frozen_binary_and_graph_match"] = True


def smoke_authored_request(python, workspace):
    stem = "Pattern-" + "0" * 32
    filenames = dict(original=stem + ".SLDPRT", spacing=stem + "-Pitch.SLDPRT", instances=stem + "-Count.SLDPRT")
    values = {"plate_x": 140000, "plate_y": 95000, "plate_z": 6000, "seed_x": 49000, "seed_y": 50000,
              "seed_dx": 10000, "seed_dy": 7000, "seed_z": 17000, "spacing": 18000, "spacing_edit": 26000}
    source = {"slot": "Slot01", "filenames": filenames, "design": case_design(values, 3)}
    case = PureWindowsPath(PRIVATE_EVAL) / "Native" / "Slot01" / "Candidates" / filenames["original"]
    plans = planned(source, case, 1795257707, pi / 4)
    evidence = {}
    for role, plan in plans.items():
        argv = (str(python), "-I", "-B", str(workspace / COMPILER))
        result = run(argv, input=encode(plan["modeled_input"]), cwd=workspace, capture_output=True, timeout=60, check=False)
        require(result.returncode == 0 and not result.stderr, "frozen 3.12 modeled projection refused\n" + result.stderr.decode())
        row = json.loads(result.stdout)
        count, pitch = row["observed"]["driver_values"][:2]
        pattern = plan["modeled_input"]["pattern"]
        independent = plan["independent_cell_measure"]
        analytic = row["analytic_geometry"]
        require(row["guarded_runtime_reads"] == 0 and count == pattern["count"] and close(pitch, pattern["pitch_m"])
                and all(close(x, y) for x, y in zip(row["observed"]["signed_direction"],
                                                   independent["signed_direction"], strict=True))
                and all(analytic[key] == independent[key] for key in ("body_count", "face_count"))
                and all(close(analytic[key], independent[key]) for key in ("volume_m3", "area_m2"))
                and all(close(x, y) for key in ("centroid_m", "bounds_m")
                        for x, y in zip(analytic[key], independent[key], strict=True)),
                "synthetic authored case lost independently predicted geometry or drivers")
        evidence[role] = row["native_container"]["sha256"]
    require(set(evidence) == set(STATES) and len(set(evidence.values())) == 1 + len(DRIVERS),
            "independent synthetic plans did not change generated content")
    return evidence


def build(prior, destination, guest_root, guest_python, local_python):
    require(prior.name == SOURCE and destination.parent == prior.parent and destination.name == TRIAL
            and not destination.exists(), "choose a new public evaluation directory adjacent to the proven intake")
    path = executable_path(guest_root)
    require(path.name == TRIAL and path.drive.casefold() == r"\\mac\home" and path.parent.name == "Oracle121Takeover",
            "incorrect public evaluation recipe transporter")
    chosen = executable_path(guest_python)
    version = check_output((str(local_python), "-I", "-B", "-c",
                            "import sys; print('.'.join(map(str,sys.version_info[:3])))"), text=True).strip()
    require(re.fullmatch(r"3\.12\.\d+", version), "use the same Python minor as the exact custodian")
    shipped = git_text("rev-parse", "HEAD")
    epoch = int(git_text("show", "-s", "--format=%ct", shipped))
    check = chronology(prior / "Public", shipped)
    cases = public_native(prior.with_name(DISCLOSED))
    comparison = smoke_comparator(prior.with_name("LinearPatternDatumHeight01") / "DisclosedHeights")
    prior_manifest = verify_source(prior / "Packet", INTAKE_SHA)
    raw = {row["path"]: checked(prior / "Packet" / row["path"], row["sha256"], row["bytes"])
           for row in prior_manifest["files"]}
    observer = git("show", OBSERVER + ":" + LANE + "/ObserveGeneratedLinearPattern.py")
    require(digest(observer) == OBSERVER_SHA, "native observer differs from pinned exact code")
    raw["Tools/ObserveGeneratedLinearPattern.py"] = observer
    for name in EVALUATION_TOOLS:
        raw["Tools/" + name] = git("show", shipped + ":" + LANE + "/evaluation/" + name)
    for name, value in raw.items():
        if name.endswith(".py"):
            parse(value, filename=name, feature_version=(3, 12))
    with TemporaryDirectory(prefix="KitPatternFreeze-") as temp:
        workspace = Path(temp).resolve()
        members, smoke = trace_compiler(local_python, workspace / "discover", cases, relevant_sources())
        raw["Compiler.zip"] = source_archive(members)
        bundle = workspace / "packet"
        bundle.mkdir()
        with (bundle / "Compiler.zip").open("xb") as archive:
            archive.write(raw["Compiler.zip"])
        inventory = {name: sha_row(value) for name, value in members.items()}
        unpack_compiler(bundle, workspace / "verify", {"compiler_members": inventory})
        smoke_compiler(local_python, workspace / "verify", cases, smoke)
        authored = smoke_authored_request(local_python, workspace / "verify")
    manifest = {
        "schema": SCHEMA, "build": BUILD, "oracle_sha256": ORACLE, "writer_revision": WRITER,
        "writer_source_tree": WRITER_TREE, "observer_revision": OBSERVER, "observer_sha256": OBSERVER_SHA,
        "evaluator_revision": shipped, "first_writer_revision": FIRST_WRITER, "source_lock_revision": SOURCE_LOCK_REVISION,
        "source_intake_sha256": INTAKE_SHA, "source_intent_sha256": INTENT_SHA, "source_lock_sha256": SOURCE_SHA,
        "disclosed_trial_sha256": DISCLOSED_TRIAL_SHA, "disclosed_result_sha256": DISCLOSED_RESULT_SHA,
        "private_source_root": PRIVATE_SOURCE, "private_evaluation_root": PRIVATE_EVAL, "guest_root": str(path),
        "control_sha256": {name: pin for name, (_, pin) in CONTROLS.items()}, "epoch": epoch,
        "complete_distinct_processes": EXPECTED_PHASES, "public_custody_chronology": check,
        "packet_files": {name: sha_row(value) for name, value in raw.items()}, "compiler_members": inventory,
        "disclosed_smoke": {"local_python": version, "cases": smoke, "comparator": comparison,
                            "authored_projection_sha256": authored, "windows_executed": False},
    }
    release = encode(manifest)
    freeze = digest(release)
    packet = destination / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    write_sources({**raw, "Freeze.json": release}, packet)
    require(verified(packet, freeze) == manifest, "fresh staged evaluation did not reproduce its public freeze")
    argv = ["prlctl", "exec", "Windows 11", "--current-user", str(chosen), "-B",
            str(path / "Packet" / "Tools" / "RunPatternEvaluation.py"), "--pin", freeze]
    result = {"schema": "kit.sw2026.oblique-linear-pattern-heldout-recipe.v1", "freeze_sha256": freeze,
              "argv": argv, "terminal_receipt": str(path / "Public" / "Result.json"), "compiler_members": len(members),
              "author_lock_already_complete": True, "host_accessed_private_payloads": False, "host_oracle_launches": 0}
    write_sources({"Recipe.json": encode(result)}, destination)
    print(encode(result).decode(), end="")


def main():
    parser = ArgumentParser()
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    parser.add_argument("--local-python312", required=True, type=Path)
    args = parser.parse_args()
    build(args.prior.resolve(), args.output, args.guest_root, args.guest_python, args.local_python312)


if __name__ == "__main__":
    main()
