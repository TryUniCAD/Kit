import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil

from DrawingEdgeCorrespondence01 import METADATA, validate

PREVIOUS_TRIAL = "47457fa53cf507373ab5a8a083897e89c486f11ae29b8eefbf164cbf8323c4bf"
PREVIOUS_FILES = "28edd6990a6b39b06e8c311f6dcdae97a9efdd347ed3d4ccdd2d4646030427b4"
PREVIOUS_RESULT = "848a20948ae30baa8a092a3ad9ec3caadf27082896f4a7d75b680c0483be7ed6"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def store(path, value):
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def freeze(args):
    base = args.source_packet.resolve(strict=True)
    output = args.output.resolve()
    require(
        not output.exists() and output.parent.is_dir(), "use an unused private packet"
    )
    require(
        digest(base / "Trial.json") == PREVIOUS_TRIAL
        and digest(base / "Files.json") == PREVIOUS_FILES
        and digest(base / "Inspection/Result.json") == PREVIOUS_RESULT,
        "the exact failed predecessor differs",
    )
    previous_result = json.loads((base / "Inspection/Result.json").read_bytes())
    require(
        previous_result["passed"] is False
        and previous_result["distinct_processes"] == 2
        and previous_result["inputs_unchanged"]
        and previous_result["encoded_slots_unchanged"]
        and not any(name.startswith("Generated") for name in previous_result["phases"]),
        "preserve the observer-only failure and unrun generated lane",
    )
    require(
        digest(args.correspondence_metadata) == METADATA,
        "registered correspondence API metadata differs",
    )
    validate(json.loads(args.correspondence_metadata.read_bytes()))
    files = json.loads((base / "Files.json").read_bytes())
    for name, row in files.items():
        path = base / name
        require(
            path.is_file()
            and path.stat().st_size == row["bytes"]
            and digest(path) == row["sha256"],
            "original frozen source changed: " + name,
        )
    output.mkdir()
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / name, target)
    for name in (
        "DrawingEdgeCorrespondence01.py",
        "DrawingEdgeBody01.py",
        "DrawingEdgeState01.py",
        "InspectDrawingEdgeQualification01.py",
    ):
        source = Path(__file__).with_name(name)
        compile(source.read_text(), str(source), "exec")
        shutil.copyfile(source, output / "Tools" / name)
    shutil.copyfile(
        args.correspondence_metadata, output / "CorrespondenceApiMetadata.json"
    )
    trial = json.loads((base / "Trial.json").read_bytes())
    cases = trial["cases"]
    trial["predecessor_observer"] = {
        key: trial[key]
        for key in (
            "observer_revision",
            "previous_trial_sha256",
            "previous_failed_result_sha256",
        )
    }
    trial.update(
        observer_revision="mapped-part-edge-owner-06",
        previous_trial_sha256=PREVIOUS_TRIAL,
        previous_failed_result_sha256=PREVIOUS_RESULT,
        correspondence_api_metadata_sha256=METADATA,
        body_ownership_rule="native-part-correspondence-and-exact-live-edge-membership-v1",
    )
    trial["tools_sha256"] = {
        path.name: digest(path) for path in sorted((output / "Tools").glob("*.py"))
    }
    require(
        trial["cases"] == cases,
        "all case geometry and annotation intent must stay unchanged",
    )
    store(output / "Trial.json", trial)
    rows = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    store(output / "Files.json", rows)
    guest = PureWindowsPath(args.guest_root)
    python = PureWindowsPath(args.guest_python)
    require(
        guest.is_absolute() and python.is_absolute(),
        "use absolute verified guest paths",
    )
    command = [
        str(python),
        "-B",
        str(guest / "Tools/InspectDrawingEdgeQualification01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--sha256", digest(output / "Trial.json")]
    store(
        output / "Recipe.json",
        {
            "schema": "kit.sw2026.drawing-edge-correspondence-retry.v1",
            "packet_sha256": digest(output / "Trial.json"),
            "commands": [
                {"name": mode, "argv": command + [mode] + tail}
                for mode in ("verify", "run")
            ],
            "root_only_serial_execution": True,
            "native_phase_order": [
                "ControlBeforeOpenEditSave",
                "ControlBeforeFreshReopen",
                "GeneratedOpenEditSave",
                "GeneratedFreshReopen",
                "ControlAfterOpenEditSave",
                "ControlAfterFreshReopen",
            ],
            "all_prior_native_and_negative_evidence_preserved": True,
            "case_inputs_and_all_other_guards_unchanged": True,
        },
    )
    return {
        "passed": True,
        "packet_sha256": digest(output / "Trial.json"),
        "recipe_sha256": digest(output / "Recipe.json"),
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-packet", type=Path, required=True)
    parser.add_argument("--correspondence-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args)))


if __name__ == "__main__":
    main()
