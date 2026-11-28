import argparse
from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path

from AuthorPlainDrawingNotes import CONTROL, ORACLE, native_phase, publish, require


TOOLS = {
    "AuthorPlainDrawingNotes.py", "AuthorCurves.py", "AuthorDrawingSources.py",
    "ObserveGeneratedNote01.py", "OracleIdentity.py", "Swapp.py",
}
ROLES = (
    "ControlBefore", "NativeNoteSource", "GeneratedOpen",
    "GeneratedEdit", "GeneratedReopen", "ControlAfter",
)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(job_path, job_sha256):
    require(digest(job_path) == job_sha256, "generated note job identity changed")
    job = loads(job_path.read_bytes())
    root = job_path.resolve().parent
    require(job["schema"] == "kit.sw2026.generated-note-origin-diagnostic.v1"
            and job["roles"] == list(ROLES)
            and job["oracle_sha256"] == ORACLE
            and job["heldout_inputs_read"] == 0,
            "unexpected native note research scope")
    require(Path(__file__).resolve().parent == root / "Tools"
            and set(job["tool_sha256"]) == TOOLS,
            "generated note native tool closure differs")
    for tool, expected in job["tool_sha256"].items():
        require(digest(root / "Tools" / tool) == expected, "native note phase tool identity changed")
    require(job["files_sha256"]["Control.SLDDRW"] == CONTROL, "expected pristine drawing control")
    expected_files = {
        "Control.SLDDRW", "Intent.json", "NativeControl/Disclosed01.SLDDRW",
        "NativeControl/Intent.json", "Candidate/PlainNativeOrigin.SLDDRW", "HostReceipt.json",
    }
    require(set(job["files_sha256"]) == expected_files, "unexpected native note file closure")
    for name, expected in job["files_sha256"].items():
        require(digest(root / name) == expected, "native note packet input changed")
    return job


def run(job_path, job_sha256):
    require(os.name == "nt", "native note phase runs only in the root-owned Windows oracle")
    job = verify(job_path, job_sha256)
    root = job_path.resolve().parent
    out = root / "Inspection"
    out.mkdir()
    candidate_key = "Candidate/PlainNativeOrigin.SLDDRW"
    native_control_key = "NativeControl/Disclosed01.SLDDRW"
    control = root / "Control.SLDDRW"
    candidate = root / candidate_key
    native_control = root / native_control_key
    intent = loads((root / "Intent.json").read_bytes())
    native_intent = loads((root / "NativeControl/Intent.json").read_bytes())
    expected = job["files_sha256"]
    resaved = out / "GeneratedNativeSaved.SLDDRW"
    require(candidate.samefile(intent["locator"]), "generated self locator and actual candidate differ")
    outcomes = {}

    arguments = {
        "ControlBefore": (None, None, CONTROL, None),
        "NativeNoteSource": (native_intent, native_control, expected[native_control_key], None),
        "GeneratedOpen": (intent, candidate, expected[candidate_key], None),
        "GeneratedEdit": (intent, candidate, expected[candidate_key], resaved),
        "ControlAfter": (None, None, CONTROL, None),
    }
    labels = {
        "ControlBefore": "control-before",
        "NativeNoteSource": "native-note-source",
        "GeneratedOpen": "generated-open",
        "GeneratedEdit": "edit",
        "GeneratedReopen": "reopen",
        "ControlAfter": "control-after",
    }
    for role in ROLES:
        directory = out / role
        if role in ("GeneratedOpen", "GeneratedEdit", "GeneratedReopen"):
            if not all(outcomes.get(key, {}).get("passed") is True for key in ("ControlBefore", "NativeNoteSource")):
                outcomes[role] = {"passed": False, "skipped": "independent controls failed"}
                continue
        if role == "GeneratedReopen":
            if not outcomes.get("GeneratedEdit", {}).get("passed"):
                outcomes[role] = {"passed": False, "skipped": "native saved result absent"}
                continue
            arguments[role] = (intent, resaved, outcomes["GeneratedEdit"]["output_sha256"], None)
        override, incoming, source_sha256, outgoing = arguments[role]
        try:
            row = native_phase(
                control, None, directory, labels[role], override, incoming,
                source_sha256, outgoing,
            )
            if override and override.get("publish_identity"):
                require(
                    row["initial_note"]["name"] == row["rebuilt_note"]["name"] == "DetailItem1",
                    "generated note lost its expected native identity",
                )
        except Exception as error:
            path = directory / "PrivateResult.json"
            row = loads(path.read_bytes()) if path.is_file() else {}
            row.update(passed=False, error={"type": type(error).__name__, "message": str(error)})
        outcomes[role] = row
        publish(out / (role + ".json"), row)
    identities = {
        row["identity"]["process_creation_filetime"]
        for row in outcomes.values() if "identity" in row
    }
    controls = all(outcomes[role].get("passed") for role in ("ControlBefore", "NativeNoteSource", "ControlAfter"))
    comparison_passed = bool(controls and len(identities) == len(ROLES) and all(row.get("passed") for row in outcomes.values()))
    verify(job_path, job_sha256)
    result = {
        "schema": "kit.sw2026.generated-note-origin-native-result.v1",
        "comparison_passed": comparison_passed,
        "controls_healthy": controls,
        "fresh_processes": len(identities),
        "results": outcomes,
        "source_immutable": True,
        "candidate_sha256": expected[candidate_key],
        "heldout_source_credit": False,
        "public_writer_qualified": False,
        "job_sha256": job_sha256,
    }
    publish(out / "Result.json", result)
    print(dumps({
        "comparison_passed": comparison_passed, "controls_healthy": controls,
        "fresh_processes": len(identities),
        "raw_result_sha256": digest(out / "Result.json"),
    }, sort_keys=True))
    return 0 if comparison_passed else 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.command == "run":
        return run(args.job, args.sha256)
    verify(args.job, args.sha256)
    print(dumps({"verified": True, "native_processes": 0, "heldout_inputs_read": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
