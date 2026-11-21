from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from subprocess import DEVNULL, STDOUT, run
from zipfile import ZipFile
import json
import os
import sys

from PatternEnvelopePacket import BUILD, ORACLE, checked, digest, encode, require
from PlanPatternEvaluation import DRIVERS, SLOTS, STATES, compare_native, planned


TRIAL = "LinearPatternDatumEvaluation01"
SOURCE = "LinearPatternDatumHoldout01"
PRIVATE_SOURCE = r"C:\KitLinearPatternDatumHoldout01"
PRIVATE_EVAL = r"C:\KitLinearPatternDatumEvaluation01"
INTAKE_SHA = "163d101c4142e47287286dcb0a074fa4f2506a9d9931783f814a5c70c8eee85a"
INTENT_SHA = "45ec6d14426febe5b05d8fdb8d5f5904fb57f0a6113dc422fa6d191d53d0f978"
SOURCE_SHA = "3b35bab5c3f7d2b1b4dfcbb7d7eedfe132ae3ddc8c0a97eb91ba7d934c6a4c76"
DISCLOSED_TRIAL_SHA = "da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1"
DISCLOSED_RESULT_SHA = "ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b"
WRITER = "d644ff7beb6b61a147a3b5de82ba5614efb155c8"
OBSERVER = "925c885153eb4be87fe6383c881f903b1fcf3cfe"
OBSERVER_SHA = "4586919bb798d1e49ef2d6d14f927af0f014901246797a15b1bd241df9033cf8"
SOURCE_LOCK_REVISION = "80b11e5b272e626012bb5f58088aa8f458e0b6c6"
FIRST_WRITER = "307e39a849a264845a9f43ad1e558d956ff9e6df"
WRITER_TREE = "a673f3586242dbd5cf5520578790316ed353b087"
SCHEMA = "kit.sw2026.oblique-linear-pattern-heldout-freeze.v1"
COMPILER = "re/tooling/sw2026/linear_pattern/LocalPatternContainerProcess.py"
EXPECTED_PHASES = 18


def verified(packet, pin):
    data = json.loads(checked(packet / "Freeze.json", pin))
    expected = {"schema": SCHEMA, "build": BUILD, "oracle_sha256": ORACLE, "writer_revision": WRITER,
                "writer_source_tree": WRITER_TREE, "observer_revision": OBSERVER, "observer_sha256": OBSERVER_SHA,
                "source_lock_revision": SOURCE_LOCK_REVISION, "first_writer_revision": FIRST_WRITER,
                "disclosed_trial_sha256": DISCLOSED_TRIAL_SHA, "disclosed_result_sha256": DISCLOSED_RESULT_SHA,
                "source_intake_sha256": INTAKE_SHA, "source_intent_sha256": INTENT_SHA, "source_lock_sha256": SOURCE_SHA,
                "private_source_root": PRIVATE_SOURCE, "private_evaluation_root": PRIVATE_EVAL,
                "complete_distinct_processes": EXPECTED_PHASES}
    require(all(data.get(key) == value for key, value in expected.items())
            and type(data["epoch"]) is int and 0 < data["epoch"] < 0x7FFFFFFF,
            "incorrect held-out code freeze")
    files = data["packet_files"]
    require(type(files) is dict and set(files) == {member.relative_to(packet).as_posix()
                                                  for member in packet.rglob("*") if member.is_file()} - {"Freeze.json"},
            "evaluation packet file closure differs")
    for name, identity in files.items():
        path = packet / name
        require(path.resolve().is_relative_to(packet) and not path.is_symlink(), "public packet member escapes its root")
        checked(path, identity["sha256"], identity["bytes"])
    checked(packet / "Tools" / "ObserveGeneratedLinearPattern.py", OBSERVER_SHA)
    return data


def unpack_compiler(packet, work, expected):
    members = expected["compiler_members"]
    require(isinstance(members, dict) and COMPILER in members, "incomplete compiler code freeze")
    with ZipFile(BytesIO((packet / "Compiler.zip").read_bytes())) as archive:
        require(len(archive.namelist()) == len(members) and set(archive.namelist()) == set(members),
                "compiler code member inventory differs")
        for name, identity in members.items():
            relative = PurePosixPath(name)
            require(relative.suffix == ".py" and relative.as_posix() == name and not relative.is_absolute()
                    and ".." not in relative.parts and "\\" not in name and ":" not in name,
                    "invalid compiler source member")
            raw = archive.read(name)
            require(len(raw) == identity["bytes"] and digest(raw) == identity["sha256"], "compiler member changed")
            path = work.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
    return work.joinpath(*PurePosixPath(COMPILER).parts)


def compiler_rows(compiler, data, *, cwd):
    payload = encode(data)
    command = (sys.executable, "-I", "-B", str(compiler))
    args = {"input": payload, "capture_output": True, "cwd": cwd, "timeout": 60, "check": False}
    result = run(command, **args)
    require(result.returncode == 0 and not result.stderr, "isolated compiler proof process refused")
    proof = json.loads(result.stdout)
    require(proof["guarded_runtime_reads"] == 0 and proof["typed_replay_count"] == 9
            and proof["observed"]["root_count"] == 24 and proof["observed"]["atom_ids"] == [101, 102, 103]
            and proof["observed"]["driver_order"] == ["D1", "D3", "D2", "D4", "D5", "D6"]
            and len(proof["streams"]) == 10, "isolated compiler did not prove the actual authored graph")
    made = []
    for _ in range(2):
        result = run((*command, "--binary"), **args)
        require(result.returncode == 0 and not result.stderr
                and len(result.stdout) == proof["native_container"]["bytes"]
                and digest(result.stdout) == proof["native_container"]["sha256"],
                "guarded binary transport differs from its independent proof")
        made.append(result.stdout)
    require(made[0] == made[1], "repeated neutral generation changed candidate content")
    return proof, made[0]


def source_freeze(shared):
    from PatternDatumHoldoutIntent import require_private_dir
    from PatternDatumHoldoutPacket import verify
    from RunPatternDatumHoldout import private_intent

    public = shared / "Public"
    private = Path(PRIVATE_SOURCE)
    require_private_dir(private / "FrozenIntent.json", private)
    intake = verify((shared / "Packet").resolve(), INTAKE_SHA)
    lock = json.loads(checked(public / "SourceLock.json", SOURCE_SHA))
    require(lock["passed"] and lock["private_data_guest_only"] is True and lock["writer_output_count"] == 0
            and lock["packet_sha256"] == INTAKE_SHA and lock["intent_lock_sha256"] == INTENT_SHA
            and lock["complete_distinct_processes"] == 16 and lock["native_build"] == BUILD
            and lock["oracle_sha256"] == ORACLE and [row["slot"] for row in lock["slots"]] == list(SLOTS)
            and len(lock["controls"]) == 4 and all(row["passed"] for row in lock["controls"]),
            "pre-writer source lock did not close its measured bracket")
    receipt, frozen = private_intent(public, private, intake, INTAKE_SHA, INTENT_SHA)
    require(lock["private_intent_sha256"] == receipt["private_intent_sha256"]
            and lock["source_revision"] == receipt["source_revision"]
            and lock["sealed_at_unix_ns"] == receipt["sealed_at_unix_ns"],
            "independent source lock changed private intent")
    return lock, frozen


def preserve_source(source_work, source, measured, directory_guard):
    root = source_work / source["slot"]
    directory_guard(root, Path(PRIVATE_SOURCE))
    require(measured["slot"] == source["slot"] and measured["passed"]
            and set(measured["native_artifacts"]) == set(STATES), "source slot does not own all three immutable saves")
    files = {role: root / source["filenames"][role] for role in STATES}
    for role, path in files.items():
        directory_guard(path, Path(PRIVATE_SOURCE))
        checked(path, measured["native_artifacts"][role])
    return files


def observed_phase(receipt, stamps, slot, stage, action):
    result, record_sha = action()
    receipt["phases"].append({"slot": slot, "role": stage, "passed": result["passed"],
                             "observation_sha256": record_sha, "checks": result["numeric_checks"]})
    if result.get("identity"):
        stamps.append(result["identity"]["process_creation_filetime"])
    require(result["passed"], "source or candidate native phase refused")
    return result


def compare_case(source, source_files, measured, expected, home, compiler, api, receipt, stamps, directory_guard):
    from ObservePatternEvaluation import observe

    slot = source["slot"]
    root = home / "Candidates"
    root.mkdir(exist_ok=False)
    directory_guard(root, Path(PRIVATE_EVAL))
    sources = {}
    baseline = expected["original"]

    for role, source_path in source_files.items():
        stage = f"source-{role}"
        result = observed_phase(receipt, stamps, slot, stage, lambda: observe(
            home, stage, source_path, {"sha256": measured["native_artifacts"][role]}, baseline, expected[role], api))
        sources[role] = result["rebuilt"]
    require(all(record["tree"] == sources["original"]["tree"]
                and record["dependencies"] == sources["original"]["dependencies"] for record in sources.values()),
            "independent source edits do not preserve the full feature tree")
    path = root / source["filenames"]["original"]
    directory_guard(path, Path(PRIVATE_EVAL))
    proof, payload = compiler_rows(compiler, baseline["modeled_input"], cwd=home)
    with path.open("xb") as stream:
        stream.write(payload)
    source_sha = proof["native_container"]["sha256"]
    source_row = {"slot": slot, "generated_sha256": source_sha, "guarded_processes": 3,
                  "runtime_input_reads": proof["guarded_runtime_reads"], "source_initial_sha256": measured["native_artifacts"]["original"],
                  "passed": False, "compared_snapshots": 0, "saved_derivatives": {}}
    receipt["cases"].append(source_row)
    for role in DRIVERS:
        stage = f"{role}-edit"
        derivative = root / source["filenames"][role]
        directory_guard(derivative, Path(PRIVATE_EVAL))
        edited = observed_phase(receipt, stamps, slot, stage, lambda: observe(
            home, stage, path, {"sha256": source_sha}, baseline, expected[role], api, edit_role=role, destination=derivative))
        compare_native(edited["rebuilt"], sources["original"])
        compare_native(edited["edited"], sources[role])
        source_row["compared_snapshots"] += 2
        stage = f"{role}-reopen"
        reopened = observed_phase(receipt, stamps, slot, stage, lambda: observe(
            home, stage, derivative, edited["saved"], baseline, expected[role], api))
        compare_native(reopened["rebuilt"], sources[role])
        compare_native(reopened["rebuilt"], edited["edited"])
        source_row["compared_snapshots"] += 1
        source_row["saved_derivatives"][role] = {"sha256": edited["saved"]["sha256"], "reopened": True}
        checked(path, source_sha)
    source_row["passed"] = True


def worker(packet, pin):
    from PatternDatumHoldoutIntent import require_private_dir
    from RunPatternDatumHoldout import observe_controls, preserve_controls, publish
    from RunPatternDatumHeight import registered
    import Swapp
    from PatternEnvelopeSpec import specification

    manifest = verified(packet, pin)
    public = packet.parent / "Public"
    private = Path(PRIVATE_EVAL)
    require(packet.parent.name == TRIAL and packet.resolve() == (Path(manifest["guest_root"]) / "Packet").resolve(),
            "unexpected public freeze locator")
    require_private_dir(private, private)
    work = private / "Native"
    work.mkdir(exist_ok=False)
    require_private_dir(work, private)
    shared_source = packet.parent.parent / SOURCE
    reference_sources = Path(PRIVATE_SOURCE) / "Native"
    receipt = {
        "schema": "kit.sw2026.oblique-linear-pattern-heldout-result.v1", "freeze_sha256": pin, "build": BUILD,
        "writer_revision": WRITER, "source_lock_sha256": SOURCE_SHA, "observer_revision": OBSERVER,
        "controls": [], "cases": [], "phases": [], "passed": False, "private_data_guest_only": True,
    }
    stamps, before, frozen = [], None, None
    bracket_started = False
    stage = "custody"
    try:
        require(not Swapp.application_pids(), "serial owned oracle required")
        compiler = unpack_compiler(packet, private / "Compiler", manifest)
        api = registered(packet)
        stage = "control-before"
        bracket_started = True
        rows, identities, before = observe_controls(packet, work, "before")
        receipt["controls"].extend(rows)
        stamps.extend(identities)
        require(len(rows) == 2 and all(row["passed"] for row in rows), "healthy before controls required")
        stage = "source-custody"
        source_lock, frozen = source_freeze(shared_source)
        stage = "native-comparison"
        for source, measured in zip(frozen["cases"], source_lock["slots"], strict=True):
            originals = preserve_source(reference_sources, source, measured, require_private_dir)
            slot_dir = work / source["slot"]
            slot_dir.mkdir(exist_ok=False)
            require_private_dir(slot_dir, private)
            locator = slot_dir / "Candidates" / originals["original"].name
            angle = specification()["direction_datum"]["arguments"][1]
            plans = planned(source, locator, manifest["epoch"], angle)
            compare_case(source, originals, measured, plans, slot_dir, compiler, api, receipt, stamps, require_private_dir)
            preserve_source(reference_sources, source, measured, require_private_dir)
        stage = "native-complete"
    except BaseException as error:
        publish(work / "Failure.json", {"stage": stage, "error": repr(error)})
    finally:
        try:
            if bracket_started:
                rows, identities, after = observe_controls(packet, work, "after")
                receipt["controls"].extend(rows)
                stamps.extend(identities)
                require(len(rows) == 2 and all(row["passed"] for row in rows) and not Swapp.application_pids(),
                        "healthy after controls and stopped oracle required")
                if before is not None:
                    preserve_controls(before, after)
            require(verified(packet, pin) == manifest, "public evaluator inputs changed during native observation")
            if frozen is not None:
                repeated, original_intent = source_freeze(shared_source)
                require(original_intent == frozen, "sealed source intent changed during evaluation")
                for source, measured in zip(original_intent["cases"], repeated["slots"], strict=True):
                    preserve_source(reference_sources, source, measured, require_private_dir)
        except BaseException as error:
            publish(work / "FinalFailure.json", {"error": repr(error)})
            stage = "final-integrity"
        receipt["complete_distinct_processes"] = len(set(stamps))
        receipt["passed"] = bool(stage == "native-complete" and len(receipt["controls"]) == 4
                                 and [case["slot"] for case in receipt["cases"]] == list(SLOTS)
                                 and all(case["passed"] for case in receipt["cases"])
                                 and len(receipt["phases"]) == 14 and all(row["passed"] for row in receipt["phases"])
                                 and len(stamps) == EXPECTED_PHASES and stamps == sorted(set(stamps)))
        receipt["disposition"] = stage
        receipt["qualified_cases"] = len(receipt["cases"]) if receipt["passed"] else 0
        publish(public / "Result.json", receipt)
    return int(not receipt["passed"])


def transport(pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "evaluation is confined to the Windows 3.12 custodian")
    from PatternDatumHoldoutIntent import require_private_dir

    packet = Path(__file__).resolve().parents[1]
    manifest = verified(packet, pin)
    require(packet.parent.name == TRIAL and packet.resolve() == (Path(manifest["guest_root"]) / "Packet").resolve(),
            "unexpected public freeze locator")
    private = Path(PRIVATE_EVAL)
    require_private_dir(private, private)
    public = packet.parent / "Public"
    require(not private.exists() and not public.exists(), "evaluation needs a fresh private output and public receipt locator")
    private.mkdir(exist_ok=False)
    require_private_dir(private, private)
    public.mkdir(exist_ok=False)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--pin", pin, "--worker"]
    with (private / "Transport.log").open("xb") as log:
        outcome = run(command, cwd=private, stdin=DEVNULL, stdout=log, stderr=STDOUT, check=False)
    target = public / "Result.json"
    if target.is_file():
        raw = target.read_bytes()
        verdict = json.loads(raw)
        print(json.dumps({"result_sha256": digest(raw), "passed": verdict["passed"],
                          "qualified_cases": verdict["qualified_cases"]}), flush=True)
    return outcome.returncode


def main():
    parser = ArgumentParser()
    parser.add_argument("--pin", required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "evaluation is confined to the Windows 3.12 custodian")
    packet = Path(__file__).resolve().parents[1]
    if args.worker:
        return worker(packet, args.pin)
    return transport(args.pin)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        if "--worker" in sys.argv:
            raise
        print(json.dumps({"passed": False, "disposition": "transport-refused"}), flush=True)
        raise SystemExit(1)
