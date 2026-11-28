from argparse import ArgumentParser
from base64 import b64decode
from copy import deepcopy
import importlib
import json
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
RELATIVE = "re/tooling/sw2026/materials/sealed_evaluation/"
SEAL = "3223fe9d3a98c3dcf2dd14b22d766124574f4fdd"
LOCK = "dd6d63443ffa4db76bbd4d41dd0fe21c46181d22"
RETAIN = "f1b6fa80384736d7cce2758ba374b0386e5d792a"
BASE = "6094c17e881c1d6f91b34c69584a61592f762cf8"
DISCLOSED_JOB = "3289913b17116604a52279a8dca2aba788ec173a2a9f89472605ba699960c477"
DISCLOSED_RESULT = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
PUBLIC = "re/solidworks/measurements/2026/AssignedMaterialPrivateSourceLock01.json"
BUILT = (
    ("RunSealedMaterialEvaluation.py", None, RELATIVE + "RunSealedMaterialEvaluation.py"),
    ("CompareMaterialStates.py", None, RELATIVE + "CompareMaterialStates.py"),
    ("SealAssignedMaterialSources.py", SEAL, "re/tooling/sw2026/materials/SealAssignedMaterialSources.py"),
    ("RunAssignedMaterialProbe.py", RETAIN, "re/tooling/sw2026/materials/RunAssignedMaterialProbe.py"),
    ("RetainAssignedMaterial.py", RETAIN, "re/tooling/sw2026/materials/RetainAssignedMaterial.py"),
)


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def load_tools(working):
    sys.path.insert(0, str(working))
    return importlib.import_module("RunSealedMaterialEvaluation")


def fake_custody(root, disclosed, source_job, source_result, safe, seal):
    ids = ["Slot" + str(i) * 32 for i in range(2)]
    cases = [{**case, "id": slot} for case, slot in zip(source_job["cases"], ids, strict=True)]
    files = {
        "Control.SLDPRT": safe.checked(disclosed / "Control.SLDPRT", safe.CONTROL),
        **{name: ("fixture only\n" + name).encode() for name in seal.COPIED if name != "Control.SLDPRT"},
        **{"Intent/" + row["id"] + ".json": safe.encode(row) for row in cases},
    }
    job = {**source_job, "cohort_role": "sealed_original", "cases": cases,
           "tools_sha256": {name: safe.digest(files["Tools/" + name]) for name in seal.TOOLS},
           "catalog_metadata_sha256": safe.digest(files["CatalogMetadata01.json"]),
           "wrapper_shape_sha256": safe.digest(files["WrapperShape01.json"]),
           "case_intent_sha256": {slot: safe.digest(files["Intent/" + slot + ".json"]) for slot in ids}}
    files["Job.json"] = safe.encode(job)
    job_pin = safe.digest(files["Job.json"])

    preflight = {"launcher_revision": SEAL, "tool_sha256": seal.digest(Path(seal.__file__).read_bytes()),
                 "sdk_tree_before_material_writer": seal.PRE_WRITER_SRC, "prior_disclosed_result_sha256": DISCLOSED_RESULT,
                 "locked_at_utc": "2026-01-01T00:00:00+00:00", "job_sha256": job_pin,
                 "members": {name: safe.digest(value) for name, value in files.items()}}
    files["PrivatePreflight.json"] = safe.encode(preflight)
    result = {**source_result, "packet_sha256": job_pin, "cohort_role": "sealed_original", "phases": {}}
    phases = result["phases"]
    phases["ControlBefore"] = dict(source_result["phases"]["ControlBefore"])
    originals = []
    for old, slot in zip(source_job["cases"], ids, strict=True):
        prior = None
        for phase in seal.PHASES:
            name = slot + "/" + phase
            row = deepcopy(source_result["phases"][old["id"] + "/" + phase])
            data = ("synthetic immutable CAD digest payload\n" + name).encode()
            if phase != "Author":
                row["input_sha256_before"] = row["input_sha256_after"] = prior
            rec = "Inspection/" + name + "/Record.json"
            files[rec] = ("synthetic per-phase log\n" + name).encode()
            row["record_sha256"] = safe.digest(files[rec])
            if phase in seal.SAVES:
                relative = "Inspection/" + name + "/" + seal.SAVES[phase]
                files[relative] = data
                prior = safe.digest(data)
                row["file"] = {"path": str(root / relative), "sha256": prior, "bytes": len(data), "diagnostics": [True, 0, 0]}
            phases[name] = row
            if phase == "Author":
                originals.append({"case_id": slot, "source": row["file"], "observation_sha256": row["record_sha256"],
                                  "request_sha256": job["case_intent_sha256"][slot]})
    phases["ControlAfter"] = dict(source_result["phases"]["ControlAfter"])
    for role in ("ControlBefore", "ControlAfter"):
        name = "Inspection/" + role + "/Record.json"
        control = json.loads(safe.checked(disclosed / name, phases[role]["record_sha256"]))
        files[name] = safe.encode({**control, "path": str(root / "Control.SLDPRT")})
        phases[role]["record_sha256"] = safe.digest(files[name])
    lock = {"originals": originals}
    result["source_lock"] = lock
    files["Inspection/Result.json"] = (json.dumps(result, allow_nan=False) + "\n").encode()
    files["Inspection/SourceLock.json"] = safe.encode(lock)
    census = seal.summarize(result, lock, job, job_pin)
    public = {"schema": seal.SCHEMA, "passed": True, "protected_payloads_exported": 0,
              "writer_outputs": 0, "heldout_comparison_credit": 0, "launcher_revision": SEAL,
              "launcher_sha256": preflight["tool_sha256"], "pre_writer_sdk_tree": preflight["sdk_tree_before_material_writer"],
              "completed_at_utc": "2026-01-02T00:00:00+00:00", "disclosed_native_result_sha256": DISCLOSED_RESULT,
              "private_intent_commitment_sha256": safe.digest(files["PrivatePreflight.json"]),
              "primary_native_result_sha256": safe.digest(files["Inspection/Result.json"]),
              "private_original_source_lock_sha256": safe.digest(files["Inspection/SourceLock.json"]), **census}
    for name, raw in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        safe.publish(target, raw)
    return public, ids


def expect_refuse(action):
    try:
        action()
    except ValueError:
        return
    raise ValueError("material custody or reference parity accepted a synthetic fault")


def disclosed_preflight(disclosed, preparer, tool_dir):
    safe = load_tools(tool_dir)
    from CompareMaterialStates import PHASE_COMPARE, check_source_observation
    from SealAssignedMaterialSources import SAVES
    import SealAssignedMaterialSources as seal

    safe.require(disclosed.name == "NativeSourcePacket03", "host preflight accepts only the disclosed material packet")
    job = json.loads(safe.checked(disclosed / "Job.json", DISCLOSED_JOB))
    observed = json.loads(safe.checked(disclosed / "Inspection/Result.json", DISCLOSED_RESULT))
    safe.require(job["cohort_role"] == "discovery" and observed["controls_healthy"] and observed["distinct_native_processes"] == 10,
                 "disclosed control observations differ")
    with TemporaryDirectory(prefix="KitMaterialSyntheticCustody") as scratch:
        mock = Path(scratch).resolve()
        public, ids = fake_custody(mock, disclosed, job, observed, safe, seal)
        _, _, members = safe.source_chain(mock, public)
        candidate = mock / "Inspection" / ids[0] / "Swap" / SAVES["Swap"]
        raw = candidate.read_bytes()
        candidate.write_bytes(raw + b"changed")
        expect_refuse(lambda: safe.source_chain(mock, public))
        candidate.write_bytes(raw)
        intent = mock / "Intent" / (ids[1] + ".json")
        meta = intent.read_bytes()
        intent.write_bytes(meta + b"changed")
        expect_refuse(lambda: safe.source_chain(mock, public))
        intent.write_bytes(meta)
        control = mock / "Inspection" / "ControlAfter" / "Record.json"
        prior = control.read_bytes()
        control.write_bytes(prior + b"changed")
        expect_refuse(lambda: safe.source_chain(mock, public))
        control.write_bytes(prior)
        token = mock / "Inspection" / "Result.json"
        before = token.read_bytes()
        token.write_bytes(before + b"changed")
        expect_refuse(lambda: safe.source_chain(mock, public))
        token.write_bytes(before)
        safe.require(safe.source_chain(mock, public)[2] == members, "original mock authority did not restore exactly")
    method = json.loads(safe.checked(preparer / "Method.json", safe.METHOD))
    code = preparer / "CodeRoot"
    manifest = json.loads(safe.checked(preparer / "CodeManifest.json", method["code_manifest_sha256"]))["python_sha256"]
    helper = code / safe.PACKET_HELPER
    safe.checked(helper, manifest[safe.PACKET_HELPER])
    verification = run((sys.executable, "-I", "-B", str(helper), "verify", str(preparer), "--method-sha256", safe.METHOD),
                       capture_output=True, timeout=120, check=False)
    safe.require(verification.returncode == 0 and not verification.stderr and json.loads(verification.stdout)["verified"],
                 "public held-out worker packet did not verify")
    rows = {}
    checked_states = 0
    for index, case in enumerate(job["cases"], 1):
        path = PureWindowsPath(r"C:\KitMaterialDisclosedReplay01") / ("Candidate" + str(index).zfill(2) + ".SLDPRT")
        request = safe.make_request(case, job["materials"], path, 1795000220)
        proc = safe.worker(code, request)
        safe.require(proc.returncode == 0 and not proc.stderr, "frozen guarded disclosed build failed")
        generated = json.loads(proc.stdout)
        artifact = b64decode(generated.pop("artifact_base64"), validate=True)
        safe.require(safe.digest(artifact) == generated["candidate_sha256"] and generated["runtime_input_or_cad_access_attempts"] == 0,
                     "disclosed worker lost exact artifact custody")
        refusal = safe.worker(code, {**request, "scope": "full-source"})
        safe.require(refusal.returncode != 0 and not refusal.stdout and b"full source preservation requires" in refusal.stderr,
                     "full source did not fail before the disclosed worker emitted")
        for _, (phase, snapshot, key) in PHASE_COMPARE.items():
            state = observed["phases"][case["id"] + "/" + phase]["states"][snapshot]
            predicted = generated["expectations"][key]
            check_source_observation(state, predicted, case["kind"])
            checked_states += 1
        negative = deepcopy(state)
        negative["rectangle"]["relations"].pop()
        expect_refuse(lambda: check_source_observation(negative, predicted, case["kind"]))
        rows[case["kind"]] = {"candidate_sha256": generated["candidate_sha256"], "request_sha256": generated["request_sha256"],
                              "native_source_observations_agree": True, "denied_runtime_inputs": 0}
    return {"passed": True, "disclosed_source_states_compared": checked_states, "synthetic_mutations_refused": 6,
            "synthetic_source_members_verified": len(members), "full_source_refusals": 2, "guarded_workers": 4,
            "protected_inputs_read": 0, "native_processes": 0, "separate_disclosed_candidates": rows}


def freeze(args):
    sys.path.insert(0, str(HERE.parent))
    import RunSealedMaterialEvaluation as safe

    revision = args.revision
    root = args.output.resolve()
    safe.require(git("rev-parse", revision + "^").decode().strip() == BASE and
                 git("rev-parse", revision + ":src") == git("rev-parse", BASE + ":src") and
                 git("cat-file", "blob", revision + ":" + RELATIVE + HERE.name) == HERE.read_bytes(),
                 "freeze requires the exact committed companion method and unchanged SDK tree")
    tools = root / "Tools"
    tools.mkdir(parents=True, exist_ok=False)
    pins = {}
    for name, commit, path in BUILT:
        raw = git("cat-file", "blob", (revision if commit is None else commit) + ":" + path)
        pins[name] = safe.publish(tools / name, raw)
    authority = git("cat-file", "blob", LOCK + ":" + PUBLIC)
    safe.require(safe.digest(authority) == safe.AUTHORITY, "published source authority digest differs")
    safe.publish(root / "SourceAuthority.json", authority)
    receipt = disclosed_preflight(args.disclosed.resolve(strict=True), args.preparation.resolve(strict=True), tools)
    preflight = safe.publish(root / "DisclosedHostPreflight.json", safe.encode(receipt))
    method = safe.encode({"schema": safe.ENVELOPE, "authority_sha256": safe.AUTHORITY, "revision": revision,
                          "tools_sha256": pins, "preparation_method_sha256": safe.METHOD, "worker_sha256": safe.WORKER_SHA,
                          "disclosed_preflight_sha256": preflight, "scope": safe.SCOPE, "protected_inputs_read": 0, "native_processes": 0})
    pin = safe.publish(root / "EvaluationMethod.json", method)
    verify = run((sys.executable, "-I", "-B", str(tools / "RunSealedMaterialEvaluation.py"), "verify", "--evaluation-sha256", pin),
                 cwd=root, capture_output=True, timeout=60, check=False)
    safe.require(verify.returncode == 0 and not verify.stderr and json.loads(verify.stdout)["passed"],
                 "frozen companion did not independently verify")
    sys.stdout.buffer.write(safe.encode({"evaluation_method_sha256": pin, "disclosed_preflight_sha256": preflight,
                                         "runner_sha256": pins["RunSealedMaterialEvaluation.py"], "verified": True}))


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--revision", required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--disclosed", type=Path, required=True)
    cli.add_argument("--preparation", type=Path, required=True)
    freeze(cli.parse_args())
