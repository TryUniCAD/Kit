from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import ast
import json
import re
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4] if HERE.parent.name == "linear_pattern" else None
TOOLING = "re/tooling/sw2026"
LANE = TOOLING + "/linear_pattern"
PRIOR_PACKET = "913426870bc64edb320e6a1508521c81da677a2ef4feef80b715c7859856c1bc"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
SPEC = "a55fd0df1898f3132f1c1eba173f7ff5b8a8e1d12159e5ae9d9e91af43586287"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
PHASES = ("author", "pristine-reopen", "spacing-edit", "spacing-reopen")
REVISION_FORMAT = r"[0-9a-f]{40}"
PACKET_SCHEMA = "kit.sw2026.linear-pattern-envelope-packet.v1"
OLD_TOOLS = (
    "AuthorBlindCutSources.py", "AuthorCurves.py", "AuthorLinearPatternSources.py",
    "InspectFresh.py", "LinearPatternAuthor.py", "LinearPatternSpecs.py", "OracleIdentity.py", "Swapp.py",
)
GUEST_TOOLS = {
    **{name: LANE + "/" + name for name in (
        "AuthorPatternEnvelope.py", "PatternEnvelopePacket.py", "RunPatternEnvelope.py",
    )},
    **{name: TOOLING + "/oblique/" + name for name in (
        "AuthorObliqueCylinder.py", "ObliqueCylinderApi.py", "ObliqueCylinderInvoke.py", "ObliqueCylinderPlan.py",
    )},
    **{name: TOOLING + "/" + name for name in (
        "AuthorAssemblySources.py", "InspectCircleSketch.py", "ObserveAssemblyLoad.py",
        "ReferencePlaneDimensions.py", "ReferencePlaneSourcePlan.py",
    )},
}
METADATA = (
    "CreateDefinition.json", "CreateFeature.json", "EndCondition.json",
    "FeatureData.json", "FeatureId.json", "Result.json",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected, size=None):
    require(path.is_file() and not path.is_symlink(), "missing or linked packet member " + path.name)
    data = path.read_bytes()
    require(digest(data) == expected and (size is None or len(data) == size), "packet member digest differs " + path.name)
    return data


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def executable_path(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and ".." not in path.parts, "absolute bounded guest path required")
    return path


def expected_files():
    return {
        "Control.SLDPRT", "Spec.json",
        *("Metadata/" + name for name in METADATA),
        *("Tools/" + name for name in (*OLD_TOOLS, *GUEST_TOOLS)),
    }


def verify(packet, expected):
    manifest_path = packet / "Trial.json"
    manifest = json.loads(checked(manifest_path, expected))
    require(manifest["schema"] == PACKET_SCHEMA and manifest["cohort"] == "disclosed"
            and manifest["native_build"] == BUILD and manifest["oracle_sha256"] == ORACLE
            and manifest["source_control_sha256"] == CONTROL and manifest["spec_sha256"] == SPEC
            and manifest["prior_packet_sha256"] == PRIOR_PACKET
            and re.fullmatch(REVISION_FORMAT, manifest["research_revision"])
            and manifest["phases"] == list(PHASES), "envelope packet protocol differs")
    rows = manifest["files"]
    planned = {row["path"] for row in rows}
    require(len(planned) == len(rows) and planned == expected_files(), "unexpected immutable packet membership")
    require({path.relative_to(packet).as_posix() for path in packet.rglob("*") if path.is_file()}
            == planned | {"Trial.json"}, "unexpected frozen packet paths")
    for row in rows:
        path = packet / row["path"]
        require(path.resolve().is_relative_to(packet.resolve()), "frozen packet path escapes")
        checked(path, row["sha256"], row["bytes"])
    checked(packet / "Control.SLDPRT", CONTROL)
    checked(packet / "Spec.json", SPEC)
    return manifest


def prepare(prior, output, guest_root, guest_python):
    require(ROOT is not None and output.is_absolute() and not output.exists() and output.parent.is_dir(),
            "use a fresh absolute host trial under the managed share")
    require(not output.is_relative_to(ROOT) and not output.is_relative_to(prior)
            and prior.name == "Packet" and prior.parent.name == "LinearPatternSourcePacket03",
            "require the actual disclosed packet and a disjoint fresh destination")
    prior_rows = json.loads(checked(prior / "Packet.json", PRIOR_PACKET))["files"]
    prior_manifest = {row["path"]: row for row in prior_rows}
    files = {}
    for name in ("Control.SLDPRT", *("Metadata/" + name for name in METADATA),
                 *("Tools/" + name for name in OLD_TOOLS)):
        row = prior_manifest[name]
        files[name] = checked(prior / name, row["sha256"], row["bytes"])
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    for target, source in GUEST_TOOLS.items():
        files["Tools/" + target] = check_output(("git", "show", revision + ":" + source), cwd=ROOT)
    files["Spec.json"] = check_output((sys.executable, "-I", "-B",
                                     str(ROOT / LANE / "PatternEnvelopeSpec.py")), cwd=ROOT)
    require(digest(files["Spec.json"]) == SPEC and digest(files["Control.SLDPRT"]) == CONTROL, "specification or control differs")
    for name, data in files.items():
        if name.endswith(".py"):
            ast.parse(data, filename=name, feature_version=(3, 12))
    require(set(files) == expected_files(), "wrong immutable staging closure")
    guest_root, guest_python = executable_path(guest_root), executable_path(guest_python)
    require(guest_root.name == output.name and guest_root.parent.name == "Oracle121Takeover"
            and guest_root.drive.casefold() == r"\\mac\home", "bind the corresponding managed Mac share trial")
    manifest = {"schema": PACKET_SCHEMA, "cohort": "disclosed", "native_build": BUILD,
                "oracle_sha256": ORACLE, "research_revision": revision, "prior_packet_sha256": PRIOR_PACKET,
                "source_control_sha256": CONTROL, "spec_sha256": SPEC, "phases": list(PHASES),
                "guest_trial_root": str(guest_root), "files": [
                    {"path": name, "sha256": digest(data), "bytes": len(data)} for name, data in sorted(files.items())
                ]}
    packet = output / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = packet / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    data = encode(manifest)
    path = packet / "Trial.json"
    with path.open("xb") as stream:
        stream.write(data)
    sha = digest(data)
    verify(packet, sha)
    native_argv = ["prlctl", "exec", "Windows 11", "--current-user", str(guest_python), "-B",
                   str(guest_root / "Packet" / "Tools" / "RunPatternEnvelope.py")]
    recipe = {"schema": "kit.sw2026.linear-pattern-envelope-recipe.v1", "packet_sha256": sha,
              "verify_argv": [*native_argv, "verify", "--pin", sha],
              "run_argv": [*native_argv, "run", "--pin", sha],
              "windows_result": str(guest_root / "DisclosedTrial" / "Result.json"),
              "host_launches": 0, "native_files_generated_by_kit": 0}
    with (output / "Recipe.json").open("xb") as stream:
        stream.write(encode(recipe))
    print(encode(recipe).decode(), end="")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--prior-packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    args = parser.parse_args()
    prepare(args.prior_packet.resolve(), args.output, args.guest_root, args.guest_python)
