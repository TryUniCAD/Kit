from argparse import ArgumentParser
from base64 import b64decode
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
from zipfile import ZipFile

from ColdEllipsePacket import EPOCH, TOOLS_COLD
from EllipseModel import SCHEMA as INTENT, predict, require, validate
from EllipsePacket import BUILD, CONTROLS, ORACLE, SHARE, digest, encode, pinned_json, predictions_equal, put, sha, valid_hash
from ReadSealedEllipseSources import LOCK_SHA, SOURCE_ROOT

NAME = "GeneratedEllipseHeldout01"
GUEST = PureWindowsPath("C:/KitGeneratedEllipseHeldout01")
PUBLIC = SHARE / NAME
DISCLOSED_SHA = "5a0cb6cfe063ac3357e193c5d39ca1749f16ad26ef6e995fdb2cae0ce5244653"
DISCLOSED_RESULT_SHA = "6c71cfd01e4b681856a4bd0aaf81d6ef7d2a10af4be1bc4feb4e6bce795d2c93"
CONSTRUCTION = "1f0235b91c8ce56e66ae7e4202898dbff01777d1"
CONSTRUCTION_SRC = "392993e1c5f530d854c132482b268d1554d8c5c7"
LOCK_COMMIT = "d3a1134c18027fa8a75676cf3cc7a8b9418395b3"
WRITER_FIRST = "9e850ab36c3a7c310c031ebc79c5931dfb7f08fd"
SCHEMA = "kit.sw2026.cold-ellipse-sealed-evaluation.v1"
FROZEN = "Freeze.json"
ENTRY = "re/tooling/sw2026/ellipse_source/CompileColdEllipse.py"
SLOTS = ("Slot01", "Slot02")
EVAL_TOOLS = ("ReadSealedEllipseSources.py", "RunSealedEllipse.py")
ASSETS = {"Compiler.zip", "PrewriterLock.json", "DisclosedNativeResult.json"} | set(CONTROLS) | {
    f"Tool/{name}" for names in TOOLS_COLD.values() for name in names
} | {f"Tool/{name}" for name in EVAL_TOOLS}


def valid_life(row):
    return (type(row.get("lifetime")) is list and len(row["lifetime"]) == 2
            and all(type(value) is int and value > 0 for value in row["lifetime"]))


def verify_disclosed(receipt):
    expected = ([("before", name, None) for name in CONTROLS]
                + [(phase, None, slot) for slot in range(2) for phase in ("edit", "reopen")]
                + [("after", name, None) for name in CONTROLS])
    rows, matches = receipt["phases"], receipt["comparisons"]
    require(receipt["trial_sha256"] == DISCLOSED_SHA and receipt["oracle_build"] == BUILD
            and receipt["oracle_sha256"] == ORACLE and receipt["passed"] is True
            and receipt["healthy_controls"] is True and receipt["idle_after"] is True
            and receipt["heldout_credit"] == 0 and receipt["batch_error"] is None
            and receipt["fresh_processes"] == len(rows) == 8
            and [(row["phase"], row["control"], row["slot"]) for row in rows] == expected
            and all(row["passed"] is True and row["exit_code"] == 0 and valid_life(row)
                    and valid_hash(row["receipt_sha256"]) for row in rows)
            and all(row["checks"] > 0 for row in rows if row["control"] is None)
            and len({tuple(row["lifetime"]) for row in rows}) == 8
            and [row["slot"] for row in matches] == [0, 1]
            and all(row["passed"] is True and row["tree_rows"] == 25 and row["source_states"] == 3 for row in matches),
            "both actual disclosed native lifecycles must pass before intake")


def verify(packet, pin):
    require(packet.resolve() == packet and packet.name == "Packet", "sealed operational packet path differs")
    freeze = pinned_json(packet / FROZEN, pin)
    require(freeze["schema"] == SCHEMA and freeze["construction_revision"] == CONSTRUCTION
            and freeze["construction_src_tree"] == CONSTRUCTION_SRC and freeze["first_writer"] == WRITER_FIRST
            and freeze["lock_commit"] == LOCK_COMMIT and valid_hash(freeze["method_revision"], 40)
            and freeze["source_root"] == str(SOURCE_ROOT) and freeze["evaluation_root"] == str(GUEST)
            and freeze["disclosed_trial_sha256"] == DISCLOSED_SHA
            and freeze["disclosed_result_sha256"] == DISCLOSED_RESULT_SHA
            and set(freeze["files"]) == ASSETS
            and {item.relative_to(packet).as_posix() for item in packet.rglob("*") if item.is_file()} == ASSETS | {FROZEN},
            "sealed operational packet inventory or immutable revisions differ")
    for name, row in freeze["files"].items():
        item = packet / name
        require(item.resolve() == item and not item.is_symlink()
                and item.stat().st_size == row["bytes"] and sha(item) == row["sha256"], "sealed packet member differs")
    lock = pinned_json(packet / "PrewriterLock.json", LOCK_SHA)
    require(lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE
            and lock["writer_output_count"] == 0 and lock["heldout_writer_acceptance"] is False
            and lock["distinct_processes"] == 10 and [row["slot"] for row in lock["slots"]] == list(SLOTS)
            and lock["finished_at"] < freeze["first_writer_time"]
            and all(sha(packet / name) == value for name, value in CONTROLS.items()),
            "source chronology or independent controls differ")
    with ZipFile(packet / "Compiler.zip") as bundle:
        require(len(compiler_members(bundle)) == freeze["compiler_members"], "frozen compiler count differs")
    verify_disclosed(pinned_json(packet / "DisclosedNativeResult.json", freeze["disclosed_result_sha256"]))
    return freeze


def compiler_members(bundle):
    info = bundle.infolist()
    members = {row.filename for row in info}
    require(len(members) == len(info) and ENTRY in members and 0 < len(info) < 15000
            and sum(row.file_size for row in info) < 150_000_000, "compiler inventory differs")
    for row in info:
        path = PurePosixPath(row.filename)
        require(path.as_posix() == row.filename and not path.is_absolute() and ".." not in path.parts
                and path.parts[0] in ("src", "re", "tests") and path.suffix == ".py"
                and all(":" not in item and "\\" not in item for item in path.parts)
                and row.external_attr >> 16 == 0o100644, "unsafe compiler closure member")
    require(len({name.casefold() for name in members}) == len(members), "compiler paths alias on Windows")
    return members


def extract(archive, root):
    root.mkdir()
    with ZipFile(archive) as bundle:
        for name in sorted(compiler_members(bundle)):
            item = root / name
            item.parent.mkdir(parents=True, exist_ok=True)
            put(item, bundle.read(name))
    return root / ENTRY


def neutral(case, locator, index):
    model = {key: case[key] for key in ("name", "center_mm", "radii_mm", "depth_mm")}
    model["major_xy"] = predict(case)["unit_axes"][0][:2]
    return encode({"model": model, "locator": str(locator), "epoch": EPOCH + index * 61})


def generate(entry, wire):
    completed = subprocess.run([sys.executable, "-I", "-B", str(entry), "--deliver"], input=wire,
                               capture_output=True, check=False, timeout=90)
    require(completed.returncode == 0 and not completed.stderr, "guarded cold ellipse compiler refused the intent")
    proof = json.loads(completed.stdout)
    raw = b64decode(proof.pop("model_base64"), validate=True)
    require(proof["input_sha256"] == digest(wire) and proof["archive_sha256"] == digest(raw)
            and proof["bytes"] == len(raw) and proof["runtime_accesses"] == 0
            and proof["locator"] == json.loads(wire)["locator"] and len(proof["streams"]) == 10
            and len(proof["ellipse"]["linked_replays"]) == 2
            and all(row["exact"] for row in proof["ellipse"]["linked_replays"].values()),
            "guarded constructed archive or model-only audit differs")
    return proof, raw


def verify_guest(packet, public=False):
    require(os.name == "nt", "protected ellipse custody and native evaluation are Windows-only")
    expected = (PUBLIC if public else GUEST) / "Packet"
    require(packet.resolve() == Path(expected) and Path(__file__).resolve().parent == packet / "Tool",
            "use the fixed managed packet and its own tool")


def install(packet, pin):
    verify_guest(packet, public=True)
    verify(packet, pin)
    target = Path(GUEST) / "Packet"
    require(not target.parent.exists() and target.parent.resolve() == target.parent, "sealed evaluation guest root is occupied")
    target.mkdir(parents=True)
    for name in sorted(ASSETS | {FROZEN}):
        item = target / name
        item.parent.mkdir(exist_ok=True)
        put(item, (packet / name).read_bytes())
    verify(target, pin)


def originals(packet):
    completed = subprocess.run([sys.executable, "-I", "-B", str(packet / "Tool/ReadSealedEllipseSources.py"),
                                str(packet / "PrewriterLock.json")], capture_output=True, check=False, timeout=45)
    if completed.returncode != 0 or completed.stderr:
        failure = packet.parent / "CustodyFailure.txt"
        if not failure.exists():
            put(failure, completed.stderr)
        raise ValueError("sealed ellipse original custody failed")
    source = json.loads(completed.stdout)
    require([row["locked"]["slot"] for row in source["slots"]] == list(SLOTS)
            and len(source["controls"]) == 4 and len(source["lifetimes"]) == 10
            and all(len(row["snapshots"]) == 4 for row in source["slots"]),
            "sealed source worker did not reproduce all locked observations")
    return source


def custody_receipt(source, pin):
    return {"freeze_sha256": pin, "prewriter_lock_sha256": LOCK_SHA,
            "slots": [row["locked"] for row in source["slots"]], "source_processes": len(source["lifetimes"]),
            "source_controls": len(source["controls"]), "source_snapshots": sum(len(row["snapshots"]) for row in source["slots"]),
            "native_launches": 0, "writer_output_count": 0, "passed": True}


def publish(name, result):
    public = Path(PUBLIC / "Public")
    require(public.resolve() == public and public.is_dir() and name in ("Custody.json", "Result.json"),
            "publish redacted receipts only to the pre-created managed folder")
    receipt = public / name
    put(receipt, encode(result))
    return sha(receipt)


def paths(folder, case):
    return tuple(folder / (case["name"] + tail + ".SLDPRT") for tail in ("", "Edited"))


def worker(packet, freeze_pin, folder, phase_pin):
    from RunColdEllipseProbe import candidate_phase, control

    capture = packet.parent / "Capture"
    require(folder.resolve() == folder and folder.is_relative_to(capture), "native phase directory is outside custody")
    entry = pinned_json(folder / "Phase.json", phase_pin)
    require(entry["freeze_sha256"] == freeze_pin and not (folder / "Record.json").exists(),
            "unexpected native phase")
    role, name = entry["phase"], entry["control"]
    record = folder / "Record.json"
    if name is not None:
        require(role in ("before", "after") and name in CONTROLS and folder == capture / f"{role}-{Path(name).stem}",
                "unexpected native control")
        return control(packet / name, record, CONTROLS[name])
    from EllipseSeamObserve import inspect_api

    slot, case, proof_pin = entry["slot"], entry["case"], entry["input_sha256"]
    require(slot in SLOTS and role in ("edit", "reopen") and folder == capture / slot / role
            and valid_hash(proof_pin), "unexpected private candidate phase")
    initial, derivative = paths(folder.parent, case)
    registered = inspect_api()
    require(registered == pinned_json(capture / "RegisteredApi.json", entry["registered_api_sha256"]),
            "registered native API changed during the trial")
    return candidate_phase(derivative if role == "reopen" else initial, derivative, proof_pin, case, role, registered, record)


def launch(packet, pin, folder, phase, **fields):
    from RunEllipseSources import exact

    folder.mkdir()
    entry = {"freeze_sha256": pin, "phase": phase, "control": None} | fields
    admission = folder / "Phase.json"
    put(admission, encode(entry))
    command = [sys.executable, "-E", "-B", str(packet / "Tool/RunSealedEllipse.py"), str(packet), "--pin", pin,
               "--phase", str(folder), "--phase-pin", sha(admission)]
    try:
        result = subprocess.run(command, capture_output=True, check=False, timeout=180)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    put(folder / "Stdout.txt", stdout)
    put(folder / "Stderr.txt", stderr)
    record = folder / "Record.json"
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity", {})
    owned = exact(identity)
    if code is None and owned:
        from AuthorCurves import cleanup_owned_process

        try:
            checked = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            checked = {"error": repr(error)}
        put(folder / "TimeoutCleanup.json", encode(checked))
    passed = code == 0 and not stderr and owned and data.get("passed") is True
    if not entry["control"]:
        passed = bool(passed and data.get("job") == {"phase": phase, "source_sha256": entry["input_sha256"]}
                      and all(row["passed"] for row in data.get("checks", ())))
    summary = {"phase": phase, "slot": entry.get("slot"), "control": entry["control"], "passed": passed,
               "record_sha256": sha(record) if record.is_file() else None, "checks": len(data.get("checks", ()))}
    life = (identity["process_id"], identity["process_creation_filetime"]) if owned else None
    return summary, life, data


def compare(locked, changed, reopened):
    from ChamferModel import compare_six
    from RunColdEllipseProbe import reconcile

    original, initial_source, edited_source, final_source = locked["snapshots"]
    reference = {"tree": initial_source["tree"], "configurations": initial_source["configurations"],
                 "parents": initial_source["definition"]["parents"], "children": initial_source["definition"]["children"]}
    require(reconcile(changed, reopened, reference)["tree_rows"] == 25,
            "generated ordered tree did not preserve its actual source")

    def metrics(row):
        body, driver = row["body"], row["driver"]
        require(body["solid_count"] == 1 and body["faces"] == 3 and len(body["mass"]["com"]) == len(body["bounds_m"]) == 3
                and {cap["station"] for cap in body["caps"]} == {0, 1}
                and all(len(bounds) == 2 for bounds in body["bounds_m"]), "unproven physical ellipse topology")
        return [(row["definition"]["depth_m"], 1e-12), (driver["value_m"], 1e-12),
                (body["mass"]["volume"], 1e-21), (body["mass"]["area"], 1e-16),
                *((value, 1e-12) for value in body["mass"]["com"]), (body["lateral_area_m2"], 1e-16),
                *((cap["area_from_rim_m2"], 1e-16) for cap in sorted(body["caps"], key=lambda cap: cap["station"])),
                *((coord, 1e-12) for bounds in body["bounds_m"] for coord in bounds)]

    checks = 0
    for actual, expected in ((changed["initial"], original), (changed["initial"], initial_source),
                             (changed["edited"], edited_source), (reopened["initial"], final_source)):
        require(actual["tree"] == expected["tree"] and actual["configurations"] == expected["configurations"]
                and {key: value for key, value in actual["definition"].items() if key != "depth_m"}
                == {key: value for key, value in expected["definition"].items() if key != "depth_m"}
                and predictions_equal(actual["profile"], expected["profile"]), "paired native feature or profile owners differ")
        ai, ei = actual["driver"], expected["driver"]
        require(ai["name"].split("@")[:2] == ei["name"].split("@")[:2] == ["D1", "EllipseBoss"]
                and ai["state"] == ei["state"] and ai["readonly"] is ei["readonly"] is False, "actual driving D1 differs")
        for (value, zero), (baseline, _) in zip(metrics(actual), metrics(expected), strict=True):
            require(compare_six(value, baseline, zero)[2], "paired native numerical observation differs")
            checks += 1
    edited = changed["driver_edit"]
    require(edited["setter_status"] == locked["driver_edit"]["setter_status"]
            and edited["requested_m"] == locked["driver_edit"]["requested_m"], "paired driving D1 edit request differs")
    return {"paired_states": 4, "paired_numeric_checks": checks, "ordered_tree_rows": 25, "editable_drivers": 1}


def evaluate(packet, pin, custody_pin):
    import Swapp
    from EllipseSeamObserve import inspect_api

    require(valid_hash(custody_pin) and not Swapp.application_pids() and not Swapp.owned_process_ids(),
            "evaluation requires an exact custody receipt and idle oracle")
    source = originals(packet)
    require(pinned_json(Path(PUBLIC / "Public/Custody.json"), custody_pin) == custody_receipt(source, pin),
            "custody-only receipt does not bind this exact lock")
    root = packet.parent
    require(not (root / "Capture").exists() and not (root / "Compiler").exists(), "evaluation may only use fresh guest destinations")
    compiler = extract(packet / "Compiler.zip", root / "Compiler")
    capture = root / "Capture"
    capture.mkdir()
    phases, lives, slots, failed = [], [], [], []
    native_error = None

    def observe(folder, phase, **fields):
        summary, lifetime, data = launch(packet, pin, folder, phase, **fields)
        phases.append(summary)
        if lifetime is not None:
            lives.append(lifetime)
        return summary, data

    def bracket(role):
        for name in CONTROLS:
            try:
                observe(capture / f"{role}-{Path(name).stem}", role, control=name)
            except Exception as error:
                failed.append({"phase": role, "control": name, "error": repr(error)})

    try:
        bracket("before")
        if len(phases) == 2 and all(row["passed"] for row in phases):
            metadata = capture / "RegisteredApi.json"
            put(metadata, encode(inspect_api()))
            source_cases = validate({"schema": INTENT,
                                     "cohort": "heldout", "cases": [row["case"] for row in source["slots"]]}, "heldout")
            for index, (slot, case, locked) in enumerate(zip(SLOTS, source_cases, source["slots"], strict=True)):
                folder = capture / slot
                folder.mkdir()
                try:
                    initial, derivative = paths(folder, case)
                    wire = neutral(case, initial, index)
                    proof, raw = generate(compiler, wire)
                    second_proof, second = generate(compiler, wire)
                    require(second == raw and second_proof == proof
                            and proof["archive_sha256"] not in (locked["locked"]["original_sha256"], locked["locked"]["edited_sha256"]),
                            "generated outputs are nondeterministic or equal to a saved source")
                    put(initial, raw)
                    put(folder / "Generation.json", encode(proof))
                    phase = {"slot": slot, "case": case, "registered_api_sha256": sha(metadata)}
                    edit, changed = observe(folder / "edit", "edit", input_sha256=proof["archive_sha256"], **phase)
                    require(edit["passed"] and derivative.is_file() and sha(initial) == proof["archive_sha256"]
                            and sha(derivative) == changed["artifact_sha256"], "native edit or save failed")
                    opened, fresh = observe(folder / "reopen", "reopen", input_sha256=changed["artifact_sha256"], **phase)
                    require(opened["passed"] and sha(derivative) == changed["artifact_sha256"], "fresh native reopen failed")
                    paired = compare(locked, changed, fresh)
                    slots.append({"slot": slot, "passed": True, "generated_sha256": proof["archive_sha256"],
                                  "edited_sha256": changed["artifact_sha256"], "guarded_writer_processes": 2,
                                  "runtime_accesses": proof["runtime_accesses"], "generated_streams": len(proof["streams"]),
                                  "linked_replays": len(proof["ellipse"]["linked_replays"])} | paired)
                except Exception as error:
                    failed.append({"slot": slot, "error": repr(error)})
                    slots.append({"slot": slot, "passed": False})
    except Exception as error:
        native_error = repr(error)
    finally:
        if not Swapp.application_pids() and not Swapp.owned_process_ids():
            bracket("after")
    put(capture / "Failures.json", encode({"batch": native_error, "phases": failed}))
    unchanged = originals(packet) == source
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    controls = [row for row in phases if row["control"]]
    valid_controls = len(controls) == 4 and all(row["passed"] for row in controls)
    separate_lifetimes = len(lives) == len(set(lives)) == 8 and not set(lives).intersection(map(tuple, source["lifetimes"]))
    passed = bool(unchanged and idle and valid_controls and separate_lifetimes and not failed and native_error is None
                  and len(phases) == 8 and len(slots) == 2 and all(row["passed"] for row in slots))
    result = {"freeze_sha256": pin, "custody_sha256": custody_pin, "prewriter_lock_sha256": LOCK_SHA,
              "construction_revision": CONSTRUCTION, "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "phases": phases, "slots": slots, "fresh_processes": len(set(lives)), "healthy_controls": valid_controls,
              "source_inputs_unchanged": unchanged, "idle_after": idle, "passed": passed,
              "heldout_passed": len(slots) if passed else 0}
    put(capture / "Result.json", encode(result))
    print(json.dumps({"passed": passed, "receipt_sha256": publish("Result.json", result)}))
    return passed


def main():
    cli = ArgumentParser()
    cli.add_argument("packet", type=Path)
    cli.add_argument("--pin", required=True)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--custody", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--phase", type=Path)
    cli.add_argument("--phase-pin")
    cli.add_argument("--custody-pin")
    request = cli.parse_args()
    packet, pin = request.packet, request.pin
    if request.verify:
        verify(packet, pin)
        print(json.dumps({"freeze_sha256": pin, "verified_files": len(ASSETS), "native_launches": 0}))
    elif request.install:
        install(packet, pin)
        print(json.dumps({"freeze_sha256": pin, "installed_files": len(ASSETS), "native_launches": 0}))
    else:
        verify_guest(packet)
        verify(packet, pin)
        if request.custody:
            receipt = custody_receipt(originals(packet), pin)
            print(json.dumps({"passed": True, "custody_sha256": publish("Custody.json", receipt), "native_launches": 0}))
        elif request.phase:
            return 0 if worker(packet, pin, request.phase, request.phase_pin) else 2
        else:
            return 0 if evaluate(packet, pin, request.custody_pin) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
