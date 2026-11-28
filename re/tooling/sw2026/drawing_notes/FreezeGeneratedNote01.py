import argparse
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from shutil import copyfile


CONTROL_DIGEST = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
NATIVE_NOTE_DIGEST = "ba31c08e6e1a915509bd8d7db8962577fe0e4bcfccf6468ce4fa92ad5b4800ad"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ROLES = [
    "ControlBefore", "NativeNoteSource", "GeneratedOpen",
    "GeneratedEdit", "GeneratedReopen", "ControlAfter",
]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read_report(path):
    row = loads(path.read_bytes())
    if (
        not row["passed"] or row["native_qualified"]
        or row["runtime_input_reads"] != 0 or row["output_operations"] != ["output_write"]
        or not row["sdk_partial_note_visible"] or not row["theoretical_anchor"]
    ):
        raise ValueError("guarded fresh note report failed")
    return row


def copy_verified(src, target, expected=None):
    identity = digest(src)
    if target.exists() or expected is not None and identity != expected:
        raise ValueError("native note packet source differs or destination is used")
    target.parent.mkdir(parents=True, exist_ok=True)
    copyfile(src, target)
    if digest(target) != identity:
        raise ValueError("frozen native note copy differs")
    return identity


def publish(path, record):
    with path.open("x", encoding="utf-8") as output:
        output.write(dumps(record, sort_keys=True, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--disclosed", type=Path, required=True)
    args = parser.parse_args()
    proof = args.proof
    packet = args.packet
    primary, other = (read_report(proof / filename) for filename in ("PrimaryA.json", "VariantA.json"))
    if (
        primary != read_report(proof / "PrimaryB.json")
        or other != read_report(proof / "VariantB.json")
        or primary["definition_length"] == other["definition_length"]
        or primary["map_counter"] == other["map_counter"]
        or primary["container_sha256"] == other["container_sha256"]
    ):
        raise ValueError("note input growth and deterministic pair agreement not proved")
    if (
        digest(packet / "Candidate/PlainNativeOrigin.SLDDRW") != primary["container_sha256"]
        or digest(packet / "Intent.json") != primary["intent_sha256"]
        or digest(proof / "Variant.json") != other["intent_sha256"]
        or digest(proof / "PrimaryRepeat.SLDDRW") != primary["container_sha256"]
        or any(digest(proof / suffix) != other["container_sha256"] for suffix in ("VariantA.SLDDRW", "VariantB.SLDDRW"))
    ):
        raise ValueError("root guarded note output or intent differs")
    tooling = args.code / "re/tooling/sw2026"
    source = tooling / "drawing_notes"
    guard = tooling / "blank_eval/rewrite/BlankRewriteGuard.py"
    programs = {
        name: digest(source / name)
        for name in ("BuildNoteArchive.py", "NoteConstruction.py", "GuardFreshNoteBuild.py", "FreezeGeneratedNote01.py")
    } | {"BlankRewriteGuard.py": digest(guard)}
    host = {
        "schema": "kit.sw2026.fresh-plain-note-origin-host.v1",
        "passed": True,
        "program_sha256": programs,
        "source_module_identification_rea": "ev_039080813e4811f6d7a52ae823dbdf1176dd0afe9d09200735f51c1fda4481ea",
        "guarded_processes": 4,
        "runtime_input_reads": 0,
        "heldout_inputs_read": 0,
        "native_processes": 0,
        "paired_outputs_byte_identical": True,
        "source_dependent_definition_and_map_lengths": True,
        "primary": primary,
        "variant": other,
        "raw_reports_sha256": {name: digest(proof / name) for name in (
            "PrimaryA.json", "PrimaryB.json", "VariantA.json", "VariantB.json",
        )},
    }
    files = {
        "Control.SLDDRW": copy_verified(args.disclosed / "Control.SLDDRW", packet / "Control.SLDDRW", CONTROL_DIGEST),
        "NativeControl/Disclosed01.SLDDRW": copy_verified(
            args.disclosed / "Disclosed01/Disclosed01.SLDDRW",
            packet / "NativeControl/Disclosed01.SLDDRW", NATIVE_NOTE_DIGEST,
        ),
        "NativeControl/Intent.json": copy_verified(
            args.disclosed / "Disclosed01/Intent.json", packet / "NativeControl/Intent.json",
        ),
        "Candidate/PlainNativeOrigin.SLDDRW": primary["container_sha256"],
        "Intent.json": primary["intent_sha256"],
    }
    report = packet / "HostReceipt.json"
    publish(report, host)
    files["HostReceipt.json"] = digest(report)
    tools = {
        name: copy_verified(tooling / name, packet / "Tools" / name)
        for name in ("AuthorCurves.py", "AuthorDrawingSources.py", "OracleIdentity.py", "Swapp.py")
    }
    tools.update({
        name: copy_verified(source / name, packet / "Tools" / name)
        for name in ("AuthorPlainDrawingNotes.py", "ObserveGeneratedNote01.py")
    })
    job = packet / "Job.json"
    publish(job, {
        "schema": "kit.sw2026.generated-note-origin-diagnostic.v1",
        "oracle_sha256": ORACLE,
        "roles": ROLES,
        "files_sha256": files,
        "tool_sha256": tools,
        "heldout_inputs_read": 0,
    })
    print(dumps({"job_sha256": digest(job), "host_receipt_sha256": digest(report), "frozen_files": len(files) + len(tools)}))


if __name__ == "__main__":
    main()
