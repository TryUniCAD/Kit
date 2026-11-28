from argparse import ArgumentParser
from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from math import dist, isclose
from pathlib import Path, PurePosixPath, PureWindowsPath
from subprocess import run, TimeoutExpired
from zipfile import ZipFile
import json
import os
import sys

from ChamferComparison import compare_state, driver_roles
from ChamferModel import ROLES, values_si
from ChamferNeutralIntent import neutral_intent
from ChamferPacket import TOOL_FILES, valid_hash, verify, write_new
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes
from RunChamferSources import PHASES, case_paths, verify_lifecycle
from RunNativeChamferProbe import expected_at
from SealChamferSources import passed_source_lock, pin_record

FAMILY = "re/tooling/sw2026/edge_chamfer_source"
ENTRY = f"{FAMILY}/sealed/CompileSealedChamfer.py"
TOOLS = {"RunSealedChamfer.py", "ObserveSealedChamfer.py", "ChamferComparison.py", "ChamferNeutralIntent.py"}
WRITER = "e117feb05923400ff9178e47c69050180e9b738c"
WRITER_TREE = "cfa7449ac446b9b0c228b77a8e1f469b49149747"
LOCK_REV = "5f85cef0cfcb4ebda91431c31cdc699a4a1e560d"
BOUNDARY_REV = "b72a893dfba18ad4ad1c4e7ee77a9700eeaafc49"
DRIVER_REV = "2f4a5cfc9c78bd7b2b8429d11cecec6eae59c796"
DISCLOSED_REV = "2a843076bc3fdccfc2a4056f0c55ffd8c717d4d3"
PREWRITER_FILE = "re/solidworks/measurements/2026/EdgeChamferPrivateSourceLock01.json"
DISCLOSED_FILE = "re/solidworks/measurements/2026/EdgeChamferColdNativeDisclosed01.json"
PREWRITER_SHA = "71523d573c97d6bb892556803b3c3914732664371b7e3292c54626b1fe2f7f43"
DISCLOSED_SHA = "dc30cd71f69dfc8ce96c2aae8c8014adb285e5d7c7d7587e963bdb0919930d5c"
DISCLOSED_RAW_SHA = "454f8687d8ae35134a7c374855e105181c21d40365a614ae76f443fff6b831ea"
DISCLOSED_TRIAL_SHA = "378922a6556db618fd7c94e4430f3ba31781df56970b12072a8ff4ea3043bef9"
PRIOR_FREEZE = "45bdc4f1cd7d6181f1eb7b7a5d3eb8d0c817596e28cec2b58bdb92c798dbb3d3"
PRIOR_RESULT = "4afa02ac360e5d3cb2b68981551b95636e585ef7d269510caca47316060ec198"
PRIOR_FAILURE = "2f6c6e11aa3e9bf5d37468033da0a713a6b766b38926c8375f6a23e948e3390d"
COMPILER_SHA = "af0b697f9d0cf7839ec67d2c7dd99443c4168f68c228c0c2617c18d558c12d57"
TRIAL = "GeneratedChamferHeldout02"
SOURCE_PATH = r"C:\KitEdgeChamferHeld01"
EVAL_PATH = fr"C:\Kit{TRIAL}"
SOURCE_ROOT = Path(SOURCE_PATH)
EVAL_ROOT = Path(EVAL_PATH)
SIGNED_EVAL_ROOT = Path(r"C:\KitGeneratedChamferHeldout03")
PUBLIC = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / TRIAL
PUBLIC_ASSETS = ({"Compiler.zip", "Control.SLDPRT", "DisclosedReceipt.json", "PrewriterLock.json", "PriorEvaluation.json",
                  "Tool/RunNativeChamferProbe.py"} | TOOL_FILES | {f"Tool/{name}" for name in TOOLS})
SLOTS = ("Slot01", "Slot02")
SCHEMA = "kit.sw2026.generated-chamfer-heldout-freeze.v2"
CUSTODY_SCHEMA = "kit.sw2026.sealed-chamfer-custody.v1"
EPOCH = 1795485600


def hash_bytes(data):
    return sha256(data).hexdigest()


def read_freeze(packet, pin):
    manifest = packet / "Freeze.json"
    require(valid_hash(pin) and not manifest.is_symlink(),
            "held-out evaluation requires the exact public freeze")
    data = manifest.read_bytes()
    require(hash_bytes(data) == pin, "held-out evaluation requires the exact public freeze")
    return json.loads(data)


def verified(packet, pin):
    freeze = read_freeze(packet, pin)
    expected = {"schema": SCHEMA, "construction_revision": WRITER, "construction_tree": WRITER_TREE,
                "prewriter_lock_revision": LOCK_REV, "disclosed_revision": DISCLOSED_REV, "oracle_build": BUILD,
                "oracle_sha256": ORACLE, "source_root": SOURCE_PATH, "evaluation_root": EVAL_PATH,
                "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT,
                "complete_fresh_processes": 10, "epochs": [EPOCH, EPOCH + 1]}
    require(all(freeze[key] == value for key, value in expected.items())
            and valid_hash(freeze["evaluator_revision"], 40)
            and freeze["boundary_revision"] == BOUNDARY_REV
            and freeze["driver_revision"] == DRIVER_REV, "evaluation code, source or oracle is unbound")
    verify_public_members(packet, freeze["files"], PUBLIC_ASSETS, COMPILER_SHA)
    return freeze, verify_original_public_evidence(packet)


def verify_public_members(packet, files, provided_assets, compiler_sha):
    require(set(files) == provided_assets
            and {item.relative_to(packet).as_posix() for item in packet.rglob("*") if item.is_file()}
            == provided_assets | {"Freeze.json"}, "held-out packet file closure differs")
    for name, identity in files.items():
        item = packet / name
        require(not item.is_symlink() and item.resolve().is_relative_to(packet.resolve())
                and item.stat().st_size == identity["bytes"] and digest(item) == identity["sha256"],
                "a frozen public file changed")
    require(files["Control.SLDPRT"]["sha256"] == CONTROL and files["Compiler.zip"]["sha256"] == compiler_sha,
            "independent healthy control or exact compiler differs")


def verify_original_public_evidence(packet):
    prewriter = pin_record(packet / "PrewriterLock.json", PREWRITER_SHA)
    disclosed = pin_record(packet / "DisclosedReceipt.json", DISCLOSED_SHA)
    prior = pin_record(packet / "PriorEvaluation.json", PRIOR_RESULT)
    require(prior["freeze_sha256"] == PRIOR_FREEZE and prior["failure_sha256"] == PRIOR_FAILURE
            and prior["construction_revision"] == WRITER
            and prior["source_lock_sha256"] == prewriter["source_lock_sha256"]
            and prior["passed"] is False and prior["heldout_lifecycle_credit"] == 0
            and prior["healthy_controls"] is True and prior["oracle_idle_after"] is True
            and prior["distinct_fresh_processes"] == 2 and not prior["slots"]
            and [(row["role"], row["passed"]) for row in prior["attempted_phases"]] == [("before", True), ("after", True)],
            "the preserved first trial does not identify the same incomplete evaluation")
    require(disclosed["schema"] == "kit.sw2026.generated-cold-chamfer-disclosed.v1"
            and disclosed["native_build"] == BUILD and disclosed["oracle_sha256"] == ORACLE
            and disclosed["construction_revision"] == WRITER and disclosed["trial_sha256"] == DISCLOSED_TRIAL_SHA
            and disclosed["native_result_sha256"] == DISCLOSED_RAW_SHA and disclosed["passed"] is True
            and disclosed["healthy_controls"] is True and disclosed["heldout_credit"] == 0
            and disclosed["distinct_processes"] == 6 and disclosed["lifecycle_slots"] == 2
            and disclosed["numeric_checks"] == 154, "the exact disclosed native prerequisite did not qualify")
    require(prewriter["schema"] == "kit.sw2026.edge-chamfer-prewriter-lock.v1"
            and prewriter["oracle_build"] == BUILD and prewriter["oracle_sha256"] == ORACLE
            and [slot["slot"] for slot in prewriter["slots"]] == list(SLOTS)
            and prewriter["distinct_native_processes"] == 8 and prewriter["writer_output_count"] == 0
            and prewriter["heldout_writer_acceptance"] is False, "the original native prewriter lock is incomplete")
    return prewriter


def compiler_bundle(packet, destination, identities):
    require(type(identities) is dict and ENTRY in identities and len(identities) < 12_000,
            "compiler closure is outside its frozen source inventory")
    with ZipFile(BytesIO((packet / "Compiler.zip").read_bytes())) as archive:
        members = archive.infolist()
        require(len(members) == len(identities) and {item.filename for item in members} == set(identities)
                and len({item.filename.casefold() for item in members}) == len(members)
                and sum(item.file_size for item in members) < 36_000_000,
                "compiler source inventory or size differs")
        for member in members:
            name = member.filename
            relative = PurePosixPath(name)
            identity = identities[name]
            require(relative.suffix == ".py" and relative.as_posix() == name and not relative.is_absolute()
                    and all(part not in (".", "..") for part in relative.parts)
                    and "\\" not in name and ":" not in name and not member.is_dir()
                    and (member.external_attr >> 16) & 0o170000 == 0o100000
                    and member.file_size == identity["bytes"] and member.file_size < 1_000_000,
                    "compiler bundle contains an invalid Python source member")
            data = archive.read(member)
            require(len(data) == identity["bytes"] and hash_bytes(data) == identity["sha256"],
                    "compiler source member does not match its freeze")
            path = destination.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as sink:
                sink.write(data)
    return destination.joinpath(*PurePosixPath(ENTRY).parts)


def private_path(path, root):
    require(os.name == "nt" and path.is_absolute() and path.drive.casefold() == "c:"
            and ".." not in path.parts and root.drive.casefold() == "c:"
            and path.is_relative_to(root), "protected files must remain in their owned C: root")
    require(path.resolve() == path and all(not item.is_symlink() and not item.is_junction()
                                          for item in (path, *path.parents)),
            "protected path resolves through an alias or reparse point")
    return path


def original_custody(public_lock):
    packet = private_path(SOURCE_ROOT / "Packet", SOURCE_ROOT)
    capture = private_path(SOURCE_ROOT / "Capture", SOURCE_ROOT)
    pin = public_lock["source_job_sha256"]
    job, cases, plans = verify(packet / "SourceJob.json", pin, private=True)
    require(job["cohort"] == "heldout" and Path(job["guest_packet"]) == packet and Path(job["guest_capture"]) == capture
            and all(job[field] == public_lock[field] for field in
                    ("source_revision", "source_tree", "method_job_sha256", "disclosed_lock_sha256")),
            "guest source is outside the exact pre-writer lock")
    lock = pin_record(private_path(capture / "SourceLock.json", SOURCE_ROOT), public_lock["source_lock_sha256"])
    passed_source_lock(lock, job, pin)
    require(lock["spec_sha256"] == public_lock["spec_sha256"] and lock["prediction_sha256"] == public_lock["prediction_sha256"]
            and lock["api_sha256"] == public_lock["registered_api_sha256"], "locked inputs or registered API differ")
    metadata = pin_record(private_path(capture / "RegisteredApi.json", SOURCE_ROOT), lock["api_sha256"])
    stamps = set()
    for role in ("before", "after"):
        pin = public_lock["controls"][role]
        require(lock["controls"][role]["receipt_sha256"] == pin, "locked controls differ")
        record = pin_record(private_path(capture / f"control-{role}/Record.json", SOURCE_ROOT), pin)
        stamps.add(lifetime(record, passed=True))
    source_models = []
    for index, (case, plan, source, sealed) in enumerate(zip(cases, plans, lock["sources"], public_lock["slots"], strict=True)):
        folder, initial, edited = (private_path(path, SOURCE_ROOT) for path in case_paths(capture, index, case))
        pins = (sealed["original_sha256"], sealed["edited_sha256"])
        require(source["slot"] == index and tuple(map(digest, (initial, edited))) == pins
                and pins == (source["original_sha256"], source["edited_sha256"]),
                "the two guest-private native source states changed")
        receipts = []
        for phase, row, pin in zip(PHASES, source["phases"], sealed["phase_receipt_sha256"], strict=True):
            require(row["receipt_sha256"] == pin, "guest source phase is outside the hash lock")
            record = pin_record(private_path(folder / phase / "Record.json", SOURCE_ROOT), pin)
            require(record["schema"] == "kit.sw2026.edge-chamfer-source-phase.v1"
                    and record["job"] == {"phase": phase, "case": case}
                    and all(check["passed"] for check in record["checks"]), "locked phase did not pass")
            stamps.add(lifetime(record, passed=True))
            receipts.append(record)
        outcomes = verify_lifecycle(initial, edited, receipts)
        require(outcomes["orientation"] == source["orientation"] and outcomes["tree_rows"] == source["tree_rows"],
                "the prewriter lock no longer matches the measured source")
        source_models.append((case, plan, source["orientation"], (initial, edited), pins, receipts))
    require(len(stamps) == 8 and {next(iter(case["edit"])) for case in cases} == set(ROLES),
            "prewriter lifetimes or independent D1 and D2 paths differ")
    return source_models, metadata, stamps


def lifetime(record, *, passed):
    owner = record.get("oracle_identity")
    if passed:
        require(record.get("passed") is True and owner and owner.get("file_version") == BUILD
                and owner.get("sha256") == ORACLE and owner.get("pe_machine") == "0x8664"
                and owner.get("version_matches"), "native process did not attest the exact allowed build")
    if owner:
        return owner["process_id"], owner["process_creation_filetime"]
    return None


def generate(compiler, wire, destination, evidence):
    data = job_bytes(wire)
    evidence.mkdir()
    trials = []
    for index in (1, 2):
        result = run((sys.executable, "-I", "-B", str(compiler)), input=data, capture_output=True,
                     cwd=compiler.parent, timeout=90, check=False)
        (evidence / f"Writer{index}.stderr").write_bytes(result.stderr)
        (evidence / f"Writer{index}.stdout").write_bytes(result.stdout)
        require(result.returncode == 0 and not result.stderr, "guarded compiler refused the supplied neutral owners")
        trials.append(json.loads(result.stdout))
    require(trials[0] == trials[1], "two exact isolated neutral writers differ")
    proof = trials[0]
    archive = b64decode(proof["model_base64"], validate=True)
    require(proof["schema"] == "kit.sw2026.sealed-chamfer-compiler.v1" and proof["intent_sha256"] == hash_bytes(data)
            and proof["archive_sha256"] == hash_bytes(archive) and proof["archive_bytes"] == len(archive)
            and proof["streams"] == 10 and proof["linked_streams_exact"] == proof["driver_count"] == 2
            and proof["runtime_accesses"] == 0, "guarded native byte and process receipts differ")
    with destination.open("xb") as stream:
        stream.write(archive)
    return proof


def launch(output, slot, role, phase, processes):
    phase_dir = output / (role if slot is None else f"{slot}-{role}")
    phase_dir.mkdir()
    spec = phase_dir / "Phase.json"
    write_new(spec, phase)
    command = (sys.executable, "-E", "-B", str(output / "Packet/Tool/ObserveSealedChamfer.py"),
               str(spec), digest(spec))
    record_path = phase_dir / "Record.json"
    try:
        job = run(command, capture_output=True, cwd=phase_dir, timeout=180, check=False)
        code, stdout, stderr = job.returncode, job.stdout, job.stderr
    except TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    (phase_dir / "Stdout.txt").write_bytes(stdout)
    (phase_dir / "Stderr.txt").write_bytes(stderr)
    record = json.loads(record_path.read_bytes()) if record_path.is_file() else {}
    passed = code == 0 and not stderr and record.get("passed") is True
    stamp = lifetime(record, passed=passed)
    if stamp:
        processes.append(stamp)
    if code is None and stamp:
        from AuthorCurves import cleanup_owned_process

        cleanup_owned_process(record["oracle_identity"], {"executable_sha256": ORACLE})
    return {"slot": slot, "role": role, "passed": passed,
            "numeric_checks": sum(check.get("passed") is True for check in record.get("checks", ())),
            "receipt_sha256": digest(record_path) if record_path.is_file() else None}, record


def validate_edit(record, case, constants):
    state = record["edit"]
    role = next(iter(case["edit"]))
    require(state["role"] == role and state["status"] == constants["swSetValueReturnStatus_e"]["swSetValue_Successful"]
            and state["driver"] == record["reopened"]["drivers"][role]
            and isclose(state["target_si"], values_si(case, True)[ROLES.index(role)], rel_tol=0, abs_tol=1e-12)
            and record["native_save_status"] == [True, 0, 0],
            "native edit must pass through the real prescribed driver and clean owned save")


def evaluate_slot(output, slot, model, compiler, epoch, metadata, phases, processes):
    case, plan, branch, source_files, source_pins, locked = model
    home = output / slot
    home.mkdir()
    candidate = private_path(home / f"{case['name']}.SLDPRT", output)
    derivative = private_path(home / f"{case['name']}Edited.SLDPRT", output)
    row = {"slot": slot, "passed": False, "paired_states": 0, "paired_numeric_checks": 0, "stage": "source"}
    base = {"case": case, "prediction": plan, "branch": branch, "target": str(derivative)}

    def observe(role, path, pin):
        summary, record = launch(output, slot, role, base | {"role": role, "source": str(path), "sha256": pin}, processes)
        phases.append(summary)
        require(summary["passed"], "exact native lifecycle phase refused")
        return record

    try:
        originals = [observe(role, path, pin) for role, path, pin in
                     zip(("original", "original-edited"), source_files, source_pins, strict=True)]
        for live, frozen, changed in zip(originals, locked[1:], (False, True), strict=True):
            row["paired_numeric_checks"] += compare_state(live["reopened"], frozen["reopened"], case, edited=changed)
        row["stage"] = "generation"
        wire = neutral_intent(case, branch, str(candidate), epoch)
        proof = generate(compiler, wire, candidate, home / "Generation")
        pairs = zip(proof["selected_endpoints_m"], expected_at(plan, branch, False)["source_edge"], strict=True)
        require(all(dist(a, b) <= 1e-12 for a, b in pairs), "generated physical edge differs from independent prediction")
        row.update({key: proof[key] for key in
                    ("archive_sha256", "archive_bytes", "streams", "linked_streams_exact", "runtime_accesses", "driver_count")})
        row["repeated_writers"] = 2
        row["stage"] = "native-lifecycle"
        edit = observe("edit", candidate, proof["archive_sha256"])
        validate_edit(edit, case, metadata["constants"])
        chosen = next(iter(case["edit"]))
        require(edit["edited"]["drivers"][chosen]["value_si"] != edit["reopened"]["drivers"][chosen]["value_si"]
                and edit["edited"]["body"]["native"]["volume"] != edit["reopened"]["body"]["native"]["volume"],
                "prescribed live edit did not alter both its driver and the real solid")
        saved = digest(derivative)
        require(saved == edit["artifact_sha256"] and saved != proof["archive_sha256"], "native save digest differs")
        reopened = observe("reopen", derivative, saved)
        require(reopened["artifact_sha256"] == saved and digest(candidate) == proof["archive_sha256"]
                and digest(derivative) == saved and tuple(map(digest, source_files)) == source_pins,
                "an immutable native input or saved derivative changed outside its own phase")
        row["stage"] = "source-comparison"
        for actual, original, changed, on_disk in ((edit, originals[0], False, True),
                ({"reopened": edit["edited"]}, originals[1], True, False), (reopened, originals[1], True, True)):
            row["paired_numeric_checks"] += compare_state(actual["reopened"], original["reopened"], case, edited=changed,
                                                            actual_saved=on_disk)
            row["paired_states"] += 1
        require(driver_roles(edit["reopened"], case["name"], case, False) ==
                driver_roles(reopened["reopened"], case["name"] + "Edited", case, True),
                "native save/reopen lost the two distinct live driver roles")
        row.update(passed=True, saved_sha256=saved, stage="complete")
    except Exception as issue:
        detail = home / "Failure.json"
        write_new(detail, {"stage": row["stage"], "error": repr(issue)})
        row["failure_sha256"] = digest(detail)
    return row


def guest_receipt_path(packet, name, public):
    require(os.name == "nt" and PureWindowsPath(packet) == public / "Packet",
            "execution must begin from the exact shared public preparation under Windows")
    receipt = Path(public / "Public" / name)
    parent = receipt.parent
    require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction()
            and not receipt.is_symlink() and not receipt.is_junction(), "invalid redacted receipt destination")
    return receipt


def custody_result(pin, public_lock, slots, phases, lifetimes, accesses):
    return {"schema": CUSTODY_SCHEMA, "freeze_sha256": pin, "source_lock_sha256": public_lock["source_lock_sha256"],
            "verified_source_slots": slots, "verified_source_phases": phases, "verified_prior_controls": lifetimes - phases,
            "verified_prior_lifetimes": lifetimes, "native_launches": 0, "blocked_external_accesses": accesses,
            "passed": (slots, phases, lifetimes, accesses) == (2, 6, 8, 0)}


def custody_worker(packet, pin, *, verify_packet=verified, public=PUBLIC, output=EVAL_ROOT):
    receipt = guest_receipt_path(packet, "Custody.json", public)
    require(not receipt.exists() and not private_path(output, output).exists(),
            "custody preflight requires its unused receipt and evaluation root")
    _, public_lock = verify_packet(packet, pin)
    denied = []

    def guard(event, args):
        if event.startswith(("ctypes.", "socket.", "winreg.")) or event in (
                "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork", "os.forkpty",
                "os.startfile", "os.startfile/2"):
            denied.append(event)
            raise PermissionError("custody verification cannot launch or access the native oracle")

    require(not {"Swapp", "pythoncom", "win32com"} & sys.modules.keys(), "custody preflight loaded an oracle dependency")
    sys.addaudithook(guard)
    try:
        models, _, lifetimes = original_custody(public_lock)
        result = custody_result(pin, public_lock, len(models), sum(len(row[-1]) for row in models),
                                len(lifetimes), len(denied))
        require(not {"Swapp", "pythoncom", "win32com"} & sys.modules.keys(), "custody preflight loaded an oracle dependency")
    except Exception as issue:
        result = custody_result(pin, public_lock, 0, 0, 0, len(denied))
        result["failure"] = "missing_protocol_field" if isinstance(issue, KeyError) else "source_custody_refused"
    write_new(receipt, result)
    return result["passed"]


def guest_worker(packet, pin, custody_pin, *, verify_packet=verified, public=PUBLIC, output=EVAL_ROOT):
    public_result = guest_receipt_path(packet, "Result.json", public)
    output = private_path(output, output)
    require(not output.exists() and not public_result.exists(),
            "evaluation needs both unused private custody and public receipt locations")
    frozen, public_lock = verify_packet(packet, pin)
    receipt = pin_record(guest_receipt_path(packet, "Custody.json", public), custody_pin)
    require(receipt == custody_result(pin, public_lock, 2, 6, 8, 0), "native run requires a passing exact custody preflight")
    output.mkdir()
    result = {"schema": "kit.sw2026.sealed-chamfer-native-result.v1", "freeze_sha256": pin,
              "custody_receipt_sha256": custody_pin,
              "construction_revision": frozen["construction_revision"], "oracle_build": BUILD, "oracle_sha256": ORACLE,
              "source_lock_sha256": public_lock["source_lock_sha256"], "attempted_phases": [],
              "slots": [], "passed": False, "heldout_lifecycle_credit": 0}
    phases, processes, prior_stamps = result["attempted_phases"], [], set()
    try:
        local_packet = output / "Packet"
        for name in frozen["files"].keys() - {"Compiler.zip"}:
            source, target = packet / name, local_packet / name
            data = source.read_bytes()
            require(hash_bytes(data) == frozen["files"][name]["sha256"],
                    "a public tool or control changed during transfer")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
        compiler = compiler_bundle(packet, output / "Compiler", frozen["compiler_members"])
        sys.path.insert(0, str(local_packet / "Tool"))
        import Swapp
        from ChamferApi import installed_api

        control = str(local_packet / "Control.SLDPRT")
        require(not Swapp.application_pids() and not Swapp.owned_process_ids(), "serial native oracle must begin idle")
        try:
            before, _ = launch(output, None, "before", {"role": "before", "source": control}, processes)
            phases.append(before)
            require(before["passed"], "native before-control did not pass")
            models, evidence, prior_stamps = original_custody(public_lock)
            _, metadata = installed_api(Swapp)
            require(metadata == evidence, "registered API changed from the frozen pre-writer source lock")
            write_new(output / "RegisteredApi.json", metadata)
            for slot, model, epoch in zip(SLOTS, models, frozen["epochs"], strict=True):
                result["slots"].append(evaluate_slot(output, slot, model, compiler, epoch, metadata, phases, processes))
            require(original_custody(public_lock) == (models, evidence, prior_stamps),
                    "the source or frozen native evidence changed after evaluation")
            result["source_immutability_verified"] = True
        finally:
            after, _ = launch(output, None, "after", {"role": "after", "source": control}, processes)
            phases.append(after)
            result["oracle_idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    except Exception as issue:
        detail = output / "Failure.json"
        write_new(detail, {"error": repr(issue)})
        result["failure_sha256"] = digest(detail)
    controls = [phase for phase in phases if phase["slot"] is None]
    healthy = [phase["role"] for phase in controls if phase["passed"]] == ["before", "after"]
    fresh = len(set(processes)) == len(processes) == 10 and not (set(processes) & prior_stamps)
    result.update(healthy_controls=healthy, distinct_fresh_processes=len(set(processes)), fresh_lifetime_gate=fresh)
    passed = (len(phases) == 10 and all(phase["passed"] for phase in phases) and healthy and fresh
              and result.get("source_immutability_verified") is True and result.get("oracle_idle_after") is True
              and "failure_sha256" not in result)
    credit = sum(row["passed"] for row in result["slots"]) if passed else 0
    result.update(passed=passed and credit == 2, heldout_lifecycle_credit=credit)
    write_new(public_result, result)
    return result["passed"]


def main(verify_packet=verified, public=PUBLIC, output=EVAL_ROOT):
    parser = ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--pin", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--custody-only", action="store_true")
    mode.add_argument("--custody-pin")
    args = parser.parse_args()
    if args.verify:
        freeze, _ = verify_packet(args.packet, args.pin)
        print(json.dumps({"freeze_sha256": args.pin, "compiler_members": len(freeze["compiler_members"]),
                          "complete_fresh_processes": freeze["complete_fresh_processes"]}, sort_keys=True))
    else:
        try:
            options = {"verify_packet": verify_packet, "public": public, "output": output}
            passed = (custody_worker(args.packet, args.pin, **options) if args.custody_only
                      else guest_worker(args.packet, args.pin, args.custody_pin, **options))
        except Exception:
            raise SystemExit(2) from None
        raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
