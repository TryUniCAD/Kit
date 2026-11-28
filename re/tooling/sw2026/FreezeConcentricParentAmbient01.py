import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def copy_checked(source, target, expected):
    require(digest(source) == expected, "frozen source changed: " + source.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "frozen destination already exists")
    copyfile(source, target)
    require(digest(target) == expected, "frozen copy differs")


def prepare(args):
    baseline = args.baseline_packet.resolve(strict=True)
    generated = args.generated.resolve(strict=True)
    source_root = args.source_root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "choose an unused parent ambient packet")
    source = json.loads(args.source_manifest.read_bytes())
    require(
        digest(args.source_manifest)
        == "83f825765eb6c8955818b1ace84b309e9ba25210e565320ec94daf0d01745f7c",
        "generated source closure differs",
    )
    for relative, expected in source["files"].items():
        require(
            digest(source_root / relative) == expected,
            "generated code changed: " + relative,
        )
    require(
        digest(generated / "Generation.json")
        == "a4170d4896d4ec514feba15e6d79c3d2e63a0a2bd61ca5f829defe81e57c2756",
        "parent generation receipt differs",
    )
    generation = json.loads((generated / "Generation.json").read_bytes())
    require(
        generation["parents_byte_identical"] is True
        and generation["parent_stream_changes"] == []
        and generation["constructor_runtime_io_attempts"]
        == generation["heldout_inputs_read"]
        == 0,
        "unexpected generated parent scope",
    )
    child_packet = args.child_packet.resolve(strict=True)
    require(
        digest(child_packet / "Trial.json")
        == "a62380477a13f4bb16402634307b75a14b687262c4e190bfd77dc9c8b6f89d69"
        and digest(child_packet / "Result.json")
        == "a959d6f3127b4d8ee2fb7279d312b538a2ad4dfd6ab52fa4838b4e66f145ad3b",
        "native child precondition identity differs",
    )
    native = json.loads((child_packet / "Result.json").read_bytes())
    require(
        native["diagnostic_completed"] is True
        and native["controls_healthy"] is True
        and native["distinct_processes"] == 4
        and native["warning_changed_32_to_0"] is True
        and native["file_saves"]
        == native["parameter_edits"]
        == native["heldout_inputs_read"]
        == 0,
        "native child precondition did not pass",
    )
    require(
        digest(args.name_result)
        == "fcb613c3aa4c6006b4647572ba35a81dba12b5c94e0e4a5cccfe9fb09161b157",
        "native name discriminator differs",
    )
    named = json.loads(args.name_result.read_bytes())
    require(
        named["name_probe_completed"] is True
        and named["controls_healthy"] is True
        and named["distinct_processes"] == 3,
        "native name discriminator did not complete",
    )
    original = baseline / "Trial.json"
    require(
        digest(original)
        == "5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34",
        "original observer packet differs",
    )
    guest = PureWindowsPath(args.guest_root)
    require(
        guest.is_absolute() and guest.name == output.name,
        "new packet guest locator differs",
    )
    child_job = json.loads((child_packet / "Trial.json").read_bytes())
    output.mkdir(parents=True)
    for relative, expected in child_job["files_sha256"].items():
        if relative.startswith("Baseline/"):
            copy_checked(child_packet / relative, output / relative, expected)
    copy_checked(
        args.name_observer,
        output / "Baseline/DiagnosticTools/InspectConcentricNames01.py",
        "7f602c124f8ce8d98fb4a2a1c84f88efb98be69135a35146282c38e6f6feb4ff",
    )
    for mode in ("Off", "On"):
        for name, row in generation["variants"][mode]["files"].items():
            copy_checked(
                generated / "Frozen" / mode / name,
                output / "Frozen" / mode / name,
                row["sha256"],
            )
    extras = {
        "Generation.json": generated / "Generation.json",
        "SourceManifest.json": args.source_manifest,
        "GeometryPrediction.json": child_packet / "GeometryPrediction.json",
        "AmbientIntent.json": child_packet / "AmbientIntent.json",
        "Neutral.json": child_packet / "Neutral.json",
    }
    for name, path in extras.items():
        copy_checked(path, output / name, digest(path))
    for name in ("InspectConcentricParentAmbient01.py", Path(__file__).name):
        path = Path(__file__).resolve().parent / name
        copy_checked(path, output / "Tools" / name, digest(path))
    preconditions = {
        "schema": "kit.sw2026.concentric-parent-ambient-preconditions.v1",
        "child_only_raw_result_sha256": digest(child_packet / "Result.json"),
        "child_only_controls_healthy": True,
        "child_only_distinct_processes": 4,
        "child_only_warning_off": [0, 32],
        "child_only_warning_on": [0, 0],
        "name_raw_result_sha256": digest(args.name_result),
        "name_controls_healthy": True,
        "name_distinct_processes": 3,
        "authored_occurrence_name_preservation": "failed on original disclosed generated parent",
        "native_parent_acceptance": False,
        "heldout_inputs_read": 0,
    }
    write_json(output / "Preconditions.json", preconditions)
    variants = {}
    for mode in ("Off", "On"):
        variants[mode] = {}
        for kind, suffix in (("parent", ".SLDASM"), ("child", ".SLDPRT")):
            ((name, row),) = [
                (name, row)
                for name, row in generation["variants"][mode]["files"].items()
                if name.endswith(suffix)
            ]
            variants[mode][kind] = {"file": "Frozen/" + mode + "/" + name, **row}
    intent = json.loads((output / "AmbientIntent.json").read_bytes())
    job = {
        "schema": "kit.sw2026.concentric-parent-ambient-native.v1",
        "roles": ["ControlBefore", "ParentOff", "ParentOn", "ControlAfter"],
        "scope": "same-locator byte-identical generated parent with exact measured ambient child off/on; preserve strict authored-name failure; independent ID/geometry/mate diagnostic",
        "variants": variants,
        "working_parent_guest_path": generation["same_parent_locator"],
        "working_child_guest_path": child_job["working_child_guest_path"],
        "occurrence_ids": generation["variants"]["Off"]["linked_sdk"]["occurrences"],
        "ambient_name": intent["ambient"]["NameValue"],
        "guest_runtime": child_job["guest_runtime"],
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "file_saves": 0,
        "parameter_edits": 0,
        "files_sha256": {
            path.relative_to(output).as_posix(): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    write_json(output / "Trial.json", job)
    trial_sha = digest(output / "Trial.json")
    python = job["guest_runtime"]["executable"]
    script = str(guest / "Tools/InspectConcentricParentAmbient01.py")
    trial = str(guest / "Trial.json")
    prefix = ["prlctl", "exec", "Windows 11", "--current-user", python, "-B", script]
    tail = [trial, "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.concentric-parent-ambient-recipe.v1",
        "packet_sha256": trial_sha,
        "host_verify_argv": [
            "uv",
            "run",
            "--no-project",
            "--offline",
            "--isolated",
            "--python",
            "3.11",
            "python",
            "-B",
            str(output / "Tools/InspectConcentricParentAmbient01.py"),
            "verify",
            str(output / "Trial.json"),
            "--trial-sha256",
            trial_sha,
        ],
        "guest_verify_argv": [*prefix, "verify", *tail],
        "commands": [
            {
                "role": role,
                "argv": [*prefix, "phase", *tail, "--phase", role],
                "source_control_must_pass_first": role.startswith("Parent"),
                "always_run_after_other_failure": role == "ControlAfter",
            }
            for role in job["roles"]
        ],
        "summary_argv": [*prefix, "summary", *tail],
        "progress_result": str(guest / "Result.json"),
        "control_after_independent": True,
        "source_commit_before_native_required": True,
        "native_acceptance": False,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }
    write_json(output / "Recipe.json", recipe)
    return {
        "packet": str(output),
        "packet_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "frozen_files": len(job["files_sha256"]),
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-packet", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--child-packet", type=Path, required=True)
    parser.add_argument("--name-observer", type=Path, required=True)
    parser.add_argument("--name-result", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
