from argparse import ArgumentParser
from base64 import b64decode
from dataclasses import asdict
from ntpath import basename
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import ast
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
LANE = HERE.parent.relative_to(ROOT).as_posix()
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(TOOLS)]

from InspectSdkBlindPart import tree_prediction
from PatternDatumHeightPacket import verify as verify_prior
from PatternEnvelopePacket import BUILD, ORACLE, checked, digest, encode, require
from RunPatternDatumDisplayContrast import ARMS, NATIVE_ROOT, PART, SCHEMA, TRIAL, verify
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
from interchange.serialization.Deserialize import FromData


HEIGHT_PACKET = "a193b7e1eeaa9641f92e89a8e3c6697fe6843568ffc30a410979089ef4d07ceb"
LOCK_SHA256 = "3b35bab5c3f7d2b1b4dfcbb7d7eedfe132ae3ddc8c0a97eb91ba7d934c6a4c76"
LOCK_REVISION = "80b11e5b2"
LOCK_PATH = "re/solidworks/measurements/2026/LocalLinearPatternDatumSourceLock01.json"
EPOCH = 1795092001
WIDTH = 157.375
HEIGHT = 94.625
DEPTH = 18.625
EDITED = 24.375
RESOLVED = "Contents/Config-0-ResolvedFeatures"


def prediction(width, height, depth):
    return {"body_count": 1, "volume_m3": width * height * depth,
            "area_m2": 2.0 * (width * height + height * depth + width * depth),
            "centre_of_mass_m": [width / 2.0, height / 2.0, depth / 2.0]}


def corners(width, height, depth):
    low_x, high_x = (-0.05 * width, 1.05 * width)
    low_y, high_y = (-0.05 * height, 1.05 * height)
    low_z, high_z = (-0.05 * depth, 1.05 * depth)
    return {"Top Plane": [[low_x, 0.0, low_z], [high_x, 0.0, low_z], [high_x, 0.0, high_z], [low_x, 0.0, high_z]],
            "Right Plane": [[0.0, low_y, low_z], [0.0, high_y, low_z], [0.0, high_y, high_z], [0.0, low_y, high_z]]}


def inputs():
    name = basename(PART).rsplit(".", 1)[0]
    points = ((0.0, 0.0), (WIDTH, 0.0), (WIDTH, HEIGHT), (0.0, HEIGHT))
    subset = MakePolygonCase(name, points, True)["document"]
    plan = ProjectPlain(FromData(subset))
    x, y, z, changed = [value / 1000.0 for value in (WIDTH, HEIGHT, DEPTH, EDITED)]
    require(plan.AxisValue == "z" and not plan.Reversed and abs(plan.DepthValue - z) < 1e-15,
            "the registered model must retain the independently authored stock")
    case = {"intent": {"self_path": str(NATIVE_ROOT / PART), "model_name": name, "configuration_name": plan.ConfigName,
                       "profile": plan.SketchName, "feature": plan.FeatureName, "support": plan.PlaneName,
                       "resolved_roots": 19, "sketch_lines": 4, "fixed_relations_in_user_sketch": 0,
                       "vertices_m": [[a / 1000.0, b / 1000.0] for a, b in points], "depth_m": z},
            "expected_initial": prediction(x, y, z),
            "edit": {"dimension": "D1@" + plan.FeatureName, "new_depth_m": changed, "expected": prediction(x, y, changed)},
            "display_corners_m": {"initial": corners(x, y, z), "edited": corners(x, y, changed)}}
    system = asdict(DefaultPartTree(plan.PlaneName, EPOCH, "z"))
    case["tree"] = tree_prediction({"settings": {"system": {"folders": system["FolderValues"], "cabinet_name": system["CabinetName"],
                                                           "planes": dict(system["PlaneNames"]), "origin_name": system["OriginName"]}}}, case)
    return {"document": subset, "path": str(NATIVE_ROOT / PART), "epoch": EPOCH}, case


def generate(value):
    candidate_process = HERE.with_name("EmitPatternDatumDisplayContrast.py")
    raw = encode(value)
    results = [run((sys.executable, "-I", "-B", str(candidate_process)), input=raw, cwd=ROOT, capture_output=True,
                   check=True, timeout=60) for _ in range(2)]
    first, second = results
    require(not first.stderr and not second.stderr and first.stdout == second.stdout, "guarded constructions disagree")
    model = json.loads(first.stdout)
    artifact = b64decode(model.pop("blob"), validate=True)
    require(model["passed"] and model["sized"] is value["sized"] and model["runtime_input_reads"] == 0
            and not model["native_acceptance"] and (len(artifact), digest(artifact)) == (model["bytes"], model["sha256"]),
            "malformed no-input generation receipt")
    return raw, model, artifact


def bind_pair(results):
    ordinary, variant = (value[1] for value in results)
    base, changed = ordinary["streams"], variant["streams"]
    require(set(base) == set(changed) and [name for name in base if base[name] != changed[name]] == [RESOLVED]
            and ordinary["map_counters"] == variant["map_counters"]
            and all(row["unsized_resolved_sha256"] == base[RESOLVED]["sha256"] for row in (ordinary, variant))
            and all(any(display["borders_m"]) for display in variant["displays"].values())
            and not any(any(display["borders_m"]) for display in ordinary["displays"].values()),
            "arm differs outside the model-owned principal display")


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def prepare(prior_packet, output, guest, guest_python):
    require(prior_packet.parent.name == "LinearPatternDatumHeight01" and prior_packet.name == "Packet"
            and output.name == TRIAL and output.is_absolute() and not output.exists(), "expected new disclosed managed staging")
    settings = verify_prior(prior_packet, HEIGHT_PACKET)
    guest = PureWindowsPath(guest)
    python = PureWindowsPath(guest_python)
    require(guest.drive.casefold() == r"\\mac\home" and guest.parent.name == "Oracle121Takeover" and guest.name == TRIAL
            and python.is_absolute() and python.name.casefold() == "python.exe", "unmanaged exact guest locator")
    revision = git("rev-parse", "HEAD").decode().strip()
    require(not git("diff", "HEAD", "--", "src", LANE), "freeze requires an unchanged committed constructor tree")
    for name in ("EmitPatternDatumDisplayContrast.py", "MakePatternPrincipalDisplay.py", "PatternHingeGeometry.py",
                 "PreparePatternDatumDisplayContrast.py", "RunPatternDatumDisplayContrast.py"):
        require(HERE.with_name(name).read_bytes() == git("show", f"{revision}:{LANE}/{name}"), "constructor tool is not revision-bound")
    lock = git("show", f"{LOCK_REVISION}:{LOCK_PATH}")
    require(digest(lock) == LOCK_SHA256, "public source lock hash differs")
    request, case = inputs()
    results = [generate({**request, "sized": mode}) for mode in (False, True)]
    bind_pair(results)
    files = {row["path"]: checked(prior_packet / row["path"], row["sha256"], row["bytes"])
             for row in settings["files"] if row["path"].startswith("Tools/") or row["path"] == "Control.SLDPRT"}
    for source in (TOOLS / "InspectSdkBlindPart.py", HERE.with_name("RunPatternDatumDisplayContrast.py")):
        files["Tools/" + source.name] = git("show", f"{revision}:{source.relative_to(ROOT).as_posix()}")
    files.update({"Case.json": encode(case), "PublicSourceLock.json": lock})
    arms = []
    for name, (intent, proof, artifact) in zip(ARMS, results, strict=True):
        files[name + ".SLDPRT"] = artifact
        files[name + "-Neutral.json"] = intent
        files[name + "-Guard.json"] = encode(proof)
        arms.append({"name": name, "bytes": proof["bytes"], "sha256": proof["sha256"],
                     "request_sha256": digest(intent), "guard_sha256": digest(encode(proof)),
                     "resolved_sha256": proof["streams"][RESOLVED]["sha256"]})
    for name, data in files.items():
        if name.endswith(".py"):
            ast.parse(data, filename=name, feature_version=(3, 12))
    packet = output / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    trial = {"schema": SCHEMA, "source_revision": revision, "src_tree": git("rev-parse", "HEAD:src").decode().strip(),
             "native_build": BUILD, "oracle_sha256": ORACLE, "native_acceptance": False, "private_inputs_read": 0,
             "known_public_source_lock_sha256": LOCK_SHA256, "native_locator": request["path"],
             "discriminator": {"only_changed_stream": RESOLVED, "guarded_processes_per_arm": 2}, "arms": arms,
             "files": [{"path": name, "sha256": digest(data), "bytes": len(data)} for name, data in sorted(files.items())]}
    raw = encode(trial)
    pin = digest(raw)
    for name, data in {**files, "Trial.json": raw}.items():
        write(packet / name, data)
    verify(packet, pin)
    recipe = {"trial_sha256": pin, "host_native_launches": 0, "arms": arms,
              "guest_argv": ["prlctl", "exec", "Windows 11", "--current-user", str(python), "-B",
                             str(guest / "Packet" / "Tools" / "RunPatternDatumDisplayContrast.py"), "--pin", pin]}
    write(output / "Recipe.json", encode(recipe))
    print(encode(recipe).decode(), end="")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--prior-packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    args = parser.parse_args()
    prepare(args.prior_packet.resolve(strict=True), args.output, args.guest_root, args.guest_python)
