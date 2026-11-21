from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output
import ast
import json
import re
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from PatternDatumHeightPacket import expected_files as measured_files, verify as verify_measured
from PatternDatumHoldoutIntent import SLOTS
from PatternEnvelopePacket import BUILD, LANE, ORACLE, checked, digest, encode, executable_path, require


BASE = "a869361ff0226b81346e99d2f7f18d6b18ad931f"
PREVIOUS_PACKET = "a193b7e1eeaa9641f92e89a8e3c6697fe6843568ffc30a410979089ef4d07ceb"
PREVIOUS_RESULT = "5e28d6a87d55e1de2ee31ebe57d3321fe6bf1759ccd6d6a5bb99dbb264777fb8"
SCHEMA = "kit.sw2026.linear-pattern-datum-holdout-intake.v1"
TRIAL = "LinearPatternDatumHoldout01"
PRIVATE_ROOT = r"C:\KitLinearPatternDatumHoldout01"
CONTROL_ROOT = "re/solidworks/v2026/corpus/"
CONTROLS = {
    "L1_boss.SLDPRT": ("ladder/L1_boss.SLDPRT",
                      "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"),
    "PrincipalRevolveTopForward.SLDPRT": ("principal-revolve-discovery/PrincipalRevolveTopForward.SLDPRT",
                                        "4bf2c202be9ae4fc7786e50a92c4f83dc17ea4bc80492b7173075d74f678d3f0"),
}
PHASES = ("author", "pristine-reopen", "spacing-edit", "spacing-reopen", "instances-edit", "instances-reopen")
NEW_TOOLS = ("PatternDatumHoldoutIntent.py", "PatternDatumHoldoutPacket.py", "RunPatternDatumHoldout.py",
             "PatternEnvelopeSpec.py")
REPLACED_TOOLS = ("RunPatternEnvelope.py",)
NO_COPY = frozenset({"Control.SLDPRT", "Spec.json", *("Tools/" + name for name in REPLACED_TOOLS)})


def expected_files():
    return (measured_files() - {"Control.SLDPRT", "Spec.json"}
            | {"Controls/" + name for name in CONTROLS} | {"Tools/" + name for name in NEW_TOOLS})


def verify(packet, pin):
    manifest = json.loads(checked(packet / "Intake.json", pin))
    require(manifest["schema"] == SCHEMA and manifest["cohort"] == "heldout"
            and manifest["native_build"] == BUILD and manifest["oracle_sha256"] == ORACLE
            and manifest["previous_packet_sha256"] == PREVIOUS_PACKET and manifest["previous_result_sha256"] == PREVIOUS_RESULT
            and manifest["private_root"] == PRIVATE_ROOT and manifest["slots"] == list(SLOTS)
            and manifest["phases"] == list(PHASES) and re.fullmatch("[0-9a-f]{40}", manifest["source_revision"])
            and manifest["writer_source_tree"] == "144d69996547bb67bf12c7b8b7e48e3c5a8f9de6"
            and manifest["controls"] == {name: pin for name, (_, pin) in CONTROLS.items()}, "inadmissible intake manifest")
    rows = manifest["files"]
    identifiers = {row["path"] for row in rows}
    require(len(rows) == len(identifiers) and identifiers == expected_files()
            and {file.relative_to(packet).as_posix() for file in packet.rglob("*") if file.is_file()}
            == identifiers | {"Intake.json"}, "intake file inventory differs")
    for row in rows:
        member = packet / row["path"]
        require(member.resolve().is_relative_to(packet.resolve()), "intake file does not resolve inside its owner")
        checked(member, row["sha256"], row["bytes"])
    for name, (_, control_pin) in CONTROLS.items():
        checked(packet / "Controls" / name, control_pin)
    return manifest


def prepare(prior, dest, guest_root, guest_python):
    require(HERE.parent.name == "linear_pattern" and prior.name == "LinearPatternDatumHeight01"
            and dest == prior.with_name(TRIAL) and not dest.exists(), "choose the unused new managed intake directory")
    measured = verify_measured(prior / "Packet", PREVIOUS_PACKET)
    result = json.loads(checked(prior / "DisclosedHeights" / "Result.json", PREVIOUS_RESULT))
    require(result["native_lifecycle_passed"] and result["packet_unchanged"] and result["distinct_processes"] == 6
            and result["packet_sha256"] == PREVIOUS_PACKET and all(row["passed"] for row in result["controls"].values()),
            "require the measured disclosed angle-plane source profile")
    guest_root, guest_python = executable_path(guest_root), executable_path(guest_python)
    require(guest_root.drive.casefold() == r"\\mac\home" and guest_root.name == TRIAL
            and guest_root.parent.name == "Oracle121Takeover", "wrong managed public intake locator")
    repo = HERE.parents[4]
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=repo, text=True).strip()
    check_output(("git", "merge-base", "--is-ancestor", BASE, revision), cwd=repo)
    source = check_output(("git", "rev-parse", revision + ":src"), cwd=repo, text=True).strip()
    members = {row["path"]: checked(prior / "Packet" / row["path"], row["sha256"], row["bytes"])
               for row in measured["files"] if row["path"] not in NO_COPY}
    for name in (*NEW_TOOLS, *REPLACED_TOOLS):
        members["Tools/" + name] = check_output(("git", "show", revision + ":" + LANE + "/" + name), cwd=repo)
    for name, (relative, pin) in CONTROLS.items():
        asset = check_output(("git", "show", revision + ":" + CONTROL_ROOT + relative), cwd=repo)
        require(digest(asset) == pin, "control differs from its independent source fixture")
        members["Controls/" + name] = asset
    for name, data in members.items():
        if name.endswith(".py"):
            ast.parse(data, filename=name, feature_version=(3, 12))
    require(set(members) == expected_files(), "unfrozen native authoring dependencies")
    manifest = {"schema": SCHEMA, "native_build": BUILD, "oracle_sha256": ORACLE, "cohort": "heldout",
                "source_revision": revision, "writer_source_tree": source, "private_root": PRIVATE_ROOT,
                "guest_root": str(guest_root), "slots": list(SLOTS), "phases": list(PHASES),
                "previous_packet_sha256": PREVIOUS_PACKET, "previous_result_sha256": PREVIOUS_RESULT,
                "controls": {name: pin for name, (_, pin) in CONTROLS.items()},
                "files": [{"path": name, "sha256": digest(data), "bytes": len(data)}
                          for name, data in sorted(members.items())]}
    packet = dest / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    for name, raw in {**members, "Intake.json": encode(manifest)}.items():
        target = packet / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    intake_pin = digest(encode(manifest))
    verify(packet, intake_pin)
    argv = ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-B",
            str(guest_root / "Packet" / "Tools" / "RunPatternDatumHoldout.py")]
    recipe = {"schema": "kit.sw2026.linear-pattern-datum-holdout-recipe.v1", "packet_sha256": intake_pin,
              "guest_seal_argv": [*argv, "seal", "--pin", intake_pin],
              "guest_author_argv_prefix": [*argv, "author", "--pin", intake_pin, "--intent-pin"],
              "intent_receipt": str(guest_root / "Public" / "IntentLock.json"),
              "terminal_receipt": str(guest_root / "Public" / "SourceLock.json"), "host_launches": 0}
    with (dest / "Recipe.json").open("xb") as stream:
        stream.write(encode(recipe))
    print(encode(recipe).decode(), end="")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--prior-trial", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    args = parser.parse_args()
    prepare(args.prior_trial.resolve(), args.output, args.guest_root, args.guest_python)
