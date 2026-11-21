from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
import ast
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PatternEnvelopePacket import (
    BUILD, CONTROL, LANE, ORACLE, REVISION_FORMAT, checked, digest, encode,
    executable_path, expected_files as envelope_files, require, verify as verify_envelope,
)


HERE = Path(__file__).resolve()
BASE = "07d76e51ed22510ef66eff3aaf3a4f6e459c4071"
ENVELOPE_PACKET = "60620b7cf6072b729e55f615d4d6e2b14f7e7dfb7a43407303e24e788dc1f328"
ENVELOPE_RESULT = "c46b85d6ee72bafcbb438c4f70813966fdcf37331585bdb6970b531fbb21b5be"
SPEC = "8325f3457f0e7d2a565a63d3bd4a718a70cf736d8a14d7045ca218dfe7d9354b"
SCHEMA = "kit.sw2026.linear-pattern-datum-height-packet.v1"
TRIAL = "LinearPatternDatumHeight01"
CASE_NAMES = ("Short", "Tall")
CASE_DEPTHS = (0.008625, 0.020375)
PHASES = ("author", "pristine-reopen")
NEW_TOOLS = ("AuthorPatternDatumHeight.py", "PatternDatumHeightPacket.py", "RunPatternDatumHeight.py")
SHARED_TOOLS = ("AuthorPatternEnvelope.py", "RunPatternEnvelope.py")


def expected_files():
    return envelope_files() | {"Tools/" + item for item in NEW_TOOLS}


def artifact_name(case):
    require(case in CASE_NAMES, "unknown disclosed arm")
    return "DatumHeight" + case + ".SLDPRT"


def verified_plan(path):
    spec = json.loads(checked(path, SPEC))
    require(spec["schema"] == "kit.sw2026.linear-pattern-datum-height-prospective.v1"
            and spec["build"] == BUILD and spec["cohort"] == "disclosed proposal"
            and spec["hinge"]["name"] == "EnvelopeHinge" and spec["hinge"]["axis_model"] == [0, 0, -1]
            and spec["direction_datum"]["name"] == spec["pattern"]["direction_plane"] == "EnvelopeDirection"
            and spec["pattern"]["feature_seed_name"] == "SeedBoss"
            and spec["pattern"]["selection_marks"] == {"direction": 1, "seed": 4},
            "datum and seed roles differ from the frozen source proposal")
    first, second = spec["arms"]
    require(tuple(row["seed_depth_m"] for row in spec["arms"]) == CASE_DEPTHS
            and all(row["spacing_m"] == 0.02 and row["instances"] == 2
                    and row["seed_box_m"][1][2] == row["seed_depth_m"] for row in spec["arms"])
            and [point[:2] for point in first["seed_box_m"]] == [point[:2] for point in second["seed_box_m"]],
            "disclosed arms must differ only in the height of their authored seed")
    return spec


def arm_spec(spec, case):
    arm = spec["arms"][CASE_NAMES.index(case)]
    return {**spec, "seed_box_m": arm["seed_box_m"], "expected_before_pattern": arm["prior_solid"],
            "arms": [{"spacing_m": arm["spacing_m"], "count": arm["instances"], "expected_final": arm["final_solid"]}]}


def verify(packet, pin):
    trial = json.loads(checked(packet / "Trial.json", pin))
    require(trial["schema"] == SCHEMA and trial["cohort"] == "disclosed"
            and trial["native_build"] == BUILD and trial["oracle_sha256"] == ORACLE
            and trial["control_sha256"] == CONTROL and trial["spec_sha256"] == SPEC
            and trial["prior_envelope_packet_sha256"] == ENVELOPE_PACKET
            and trial["prior_envelope_result_sha256"] == ENVELOPE_RESULT
            and re.fullmatch(REVISION_FORMAT, trial["research_revision"])
            and re.fullmatch("[0-9a-f]{64}", trial["host_audit_sha256"])
            and trial["sequence"] == [[case, phase] for case in CASE_NAMES for phase in PHASES],
            "datum-height trial protocol changed")
    files = trial["files"]
    declared = {row["path"] for row in files}
    require(declared == expected_files() and len(files) == len(declared)
            and {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()} == declared | {"Trial.json"},
            "unexpected datum-height packet membership")
    for row in files:
        target = packet / row["path"]
        require(target.resolve().is_relative_to(packet.resolve()), "datum-height packet member escaped")
        checked(target, row["sha256"], row["bytes"])
    checked(packet / "Control.SLDPRT", CONTROL)
    verified_plan(packet / "Spec.json")
    return trial


def prepare(prior, output, guest_root, guest_python):
    require(HERE.parent.name == "linear_pattern" and output.is_absolute() and not output.exists()
            and prior.name == "LinearPatternEnvelope02" and output == prior.with_name(TRIAL),
            "use the disclosed passing sibling and a new managed datum-height directory")
    previous = verify_envelope(prior / "Packet", ENVELOPE_PACKET)
    result = json.loads(checked(prior / "DisclosedTrial" / "Result.json", ENVELOPE_RESULT))
    require(result["distinct_processes"] == 6 and result["native_lifecycle_passed"]
            and result["packet_sha256"] == ENVELOPE_PACKET and result["packet_unchanged"]
            and all(row["passed"] for row in result["controls"].values()), "prior disclosed bracket did not pass")
    guest_root, guest_python = executable_path(guest_root), executable_path(guest_python)
    require(guest_root.drive.casefold() == r"\\mac\home" and guest_root.name == TRIAL
            and guest_root.parent.name == "Oracle121Takeover", "expected managed native locator")
    root = HERE.parents[4]
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=root, text=True).strip()
    check_output(("git", "merge-base", "--is-ancestor", BASE, revision), cwd=root)
    files = {}
    for row in previous["files"]:
        name = row["path"]
        if name != "Spec.json" and name not in {"Tools/" + item for item in SHARED_TOOLS}:
            files[name] = checked(prior / "Packet" / name, row["sha256"], row["bytes"])
    for item in (*NEW_TOOLS, *SHARED_TOOLS):
        files["Tools/" + item] = check_output(("git", "show", revision + ":" + LANE + "/" + item), cwd=root)
    files["Spec.json"] = check_output((sys.executable, "-I", "-B", str(HERE.with_name("PatternDatumHeightContrast.py"))))
    audit = check_output(("git", "show", revision + ":" + LANE + "/AuditPatternDatumHeight.py"), cwd=root)
    require(digest(files["Spec.json"]) == SPEC and set(files) == expected_files(),
            "datum-height independent predictions or executable closure differ")
    for name, raw in files.items():
        if name.endswith(".py"):
            ast.parse(raw, filename=name, feature_version=(3, 12))
    trial = {"schema": SCHEMA, "cohort": "disclosed", "research_revision": revision, "native_build": BUILD,
             "oracle_sha256": ORACLE, "spec_sha256": SPEC, "control_sha256": CONTROL,
             "prior_envelope_packet_sha256": ENVELOPE_PACKET, "prior_envelope_result_sha256": ENVELOPE_RESULT,
             "host_audit_sha256": digest(audit), "guest_trial_root": str(guest_root),
             "sequence": [[case, phase] for case in CASE_NAMES for phase in PHASES],
             "files": [{"path": path, "sha256": digest(data), "bytes": len(data)} for path, data in sorted(files.items())]}
    packet = output / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    for name, raw in {**files, "Trial.json": encode(trial)}.items():
        target = packet / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    pin = digest(encode(trial))
    verify(packet, pin)
    recipe = {"schema": "kit.sw2026.linear-pattern-datum-height-recipe.v1",
              "packet_sha256": pin, "prediction_sha256": SPEC, "host_launches": 0,
              "guest_argv": ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-B",
                             str(guest_root / "Packet" / "Tools" / "RunPatternDatumHeight.py"), "--pin", pin],
              "native_result": str(guest_root / "DisclosedHeights" / "Result.json")}
    with (output / "Recipe.json").open("xb") as stream:
        stream.write(encode(recipe))
    print(encode(recipe).decode(), end="")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--prior-trial", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    options = parser.parse_args()
    prepare(options.prior_trial.resolve(), options.output, options.guest_root, options.guest_python)
