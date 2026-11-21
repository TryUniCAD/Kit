from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
from importlib import import_module
from math import radians
from pathlib import Path, PureWindowsPath
from struct import unpack
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent / "EndModes"), str(HERE.parent / "Preparation"), str(HERE.parents[1])]

from AuditRevEndOwners import (
    ArchiveNode, ReadNativeLink, ReadRevOwners, SldprtArchive, digest, guard_runtime,
    observe_ends, require,
)
from AuditThinArchive import refusal
from RevolveFamilyModel import validate_specs
from RevolveStreamAudit02 import stream_audit
from ThinConstruct import construct
from ThinNeutral import MODES, make_model
from ThinWireOwners import check_open_profile, check_walls
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml

PREWRITER_LOCK = "35c607164409bff6fe2222358ac1e8b6da981782"
LOCK_SHA256 = "e81db7caf2db600543f6f85b61b3a47a27cfd4b670f8e6a55f45dc79e6637653"
LOCK_PATH = "re/solidworks/measurements/2026/RevolveThinHeldoutSourceLock01.json"
OPEN_PROFILE = "must contain two actual independent open lines"


def expected(case):
    profile_x = case["axis_x_m"] + case["profile_radius_m"]
    y0, y1 = case["axial_m"]
    a0, a1 = case["axis_axial_m"]
    profile = {"frame_points": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
               "segments": [{"kind": "line", "construction": False, "start": [profile_x, y0], "end": [profile_x, y1]}]}
    widths = case["wall_m"]
    drivers = {"angle": {"name": "D1", "value": radians(case["angle_deg"]), "editable": True, "display_scale": 1.0}}
    for index, width in enumerate(widths):
        if width:
            drivers[f"wall{index + 1}"] = {"name": f"D{3 + index}", "value": width, "editable": True, "display_scale": 1.0}
    return {"definition": {"axis": {"points": [[case["axis_x_m"], a0, 0], [case["axis_x_m"], a1, 0]]},
                           "wall_getters_m": widths}, "drivers": drivers, "profile": profile}


def measure(raw, case):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (feature,) = [node for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)
                  and node.ClassValue.NameValue == "moRevolutionThin_c"]
    angles = observe_ends(link, feature)
    require(angles["angles"]["f18"]["radians"] == radians(case["angle_deg"]) and angles["angles"]["f20"] is None
            and angles["feature_words"]["f828"] == 5 and angles["feature_words"]["f824"] == 0,
            "generated thin end did not retain the exact directed angular driver")
    spec = feature.FieldsValue["f8f0"]
    mode = MODES[case["wall_mode"]]
    require(spec.FieldsValue["f28"] == mode and spec.FieldsValue["f48"] is None
            and not feature.FieldsValue["has_f528"], "generated thin cached or switched its wall intent")
    authored = expected(case)
    profile = check_open_profile(link, feature, authored["definition"], authored["profile"])
    walls = check_walls(spec, mode, authored, profile, link)
    for slot, part in (("f08", 0), ("f10", 1)):
        value, = unpack("<d", spec.FieldsValue[slot].FieldsValue["f5b0"]["data"])
        require(value == walls[slot]["metres"], "generated display cache is not derived from its own parameter")
    keywords = ParseXml(archive.require(KeywordsStream))
    (node,) = [node for node in keywords if node.attrib.get("Type") == "Revolve-Thin"]
    names = [child.attrib["Name"] for child in node if child.tag == "Dimension"]
    require(names == (["D1", "D4", "D3"] if mode == 3 else ["D3", "D1"]),
            "generated thin keywords have the wrong actual active dimensions")
    streams, history = stream_audit(archive, link)
    require(len(streams) + len(history) == 10 and all(row["qualified"] for row in history.values()),
            "generated part has an incomplete typed stream inventory")
    ordinary = refusal(lambda: ReadRevOwners(link), "unqualified feature class")
    return {"sha256": digest(raw), "bytes": len(raw), "mode": mode, "wall_metres": {slot: walls[slot]["metres"]
            for slot in ("f08", "f10")}, "keyword_order": names, "points_mm": profile["points_mm"],
            "initializer_end_thickness_m": spec.FieldsValue["f30"], "typed_streams": streams | history,
            "ordinary_projection_refusal": ordinary}


def worker(request):
    for name in ("DocumentProvenance", "AngleRevValidate", "DocumentAssemblyValidate", "DocumentFeatureValidate",
                 "DocumentReferenceValidate", "PlaneRevValidate", "DistExtValidate"):
        package = "Models" if name == "DocumentProvenance" else "Validation"
        import_module(f"interchange.document.{package}.{name}")
    case, destination, epoch = (request[key] for key in ("case", "destination", "epoch"))
    blocked = guard_runtime()
    doc = make_model(case)
    raw, _ = construct(doc, case["wall_mode"], destination, epoch)
    repeat, _ = construct(doc, case["wall_mode"], destination, epoch)
    require(raw == repeat, "model-only construction is not deterministic")
    proof = measure(raw, case)
    slot = 1 if case["wall_mode"] == "two" else 0
    widths = list(case["wall_m"])
    widths[slot] = case["edit_wall_m"][slot]
    edit = dict(case, wall_m=widths)
    altered, _ = construct(make_model(edit), edit["wall_mode"], destination, epoch)
    contrast_proof = measure(altered, edit)
    changed = sorted(name for name, row in proof["typed_streams"].items()
                     if row != contrast_proof["typed_streams"][name])
    require(altered != raw and changed == ["Contents/Config-0-ResolvedFeatures", KeywordsStream],
            "an independent wall input must affect its resolved owner and keyword only")
    proof["independent_neutral_wall_contrast"] = {"edited_driver": f"D{3 + slot}", "sha256": digest(altered),
                                                  "different_streams": changed}
    (sketch,) = doc.sketches
    contrast = replace(doc, sketches=(replace(sketch, suppressed=True),))
    proof["suppressed_profile_refusal"] = refusal(lambda: construct(contrast, case["wall_mode"], destination, epoch),
                                                  OPEN_PROFILE)
    require(not blocked, "thin model-only builder touched external data")
    return {**proof, "runtime_external_access_attempts": 0, "candidate": b64encode(raw).decode("ascii")}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()


def build(spec_path, output, guest, epoch):
    require(output.is_absolute() and not output.resolve().is_relative_to(ROOT) and not output.exists()
            and guest.is_absolute(), "use a new external output directory and absolute native locator")
    require(run(["git", "merge-base", "--is-ancestor", PREWRITER_LOCK, "HEAD"], cwd=ROOT).returncode == 0
            and digest((ROOT / LOCK_PATH).read_bytes()) == LOCK_SHA256, "thin construction lost prewriter lock ancestry")
    require(not check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT).strip(),
            "candidate packet requires a clean tracked writer revision")
    spec_raw = spec_path.read_bytes()
    spec = json.loads(spec_raw)
    require(spec["split"] == "discovery" and spec["family"] == "thin", "this tool takes disclosed thin model inputs only")
    cases = validate_specs(spec)
    require(all(case["plane"] == "front" and not case["reverse"] for case in cases),
            "this research route requires disclosed forward Front models")
    candidates = []
    for case in cases:
        command = [sys.executable, "-B", __file__, "--worker"]
        request = {"case": case, "destination": str(guest / (case["name"] + ".SLDPRT")), "epoch": epoch}
        response = run(command, input=encode(request), capture_output=True)
        require(response.returncode == 0, response.stderr.decode())
        row = json.loads(response.stdout)
        raw = b64decode(row.pop("candidate"), validate=True)
        require(row["sha256"] == digest(raw), "candidate bytes differ from guarded worker receipt")
        candidates.append((case["name"], raw, row))
    output.mkdir()
    for name, raw, _ in candidates:
        (output / (name + ".SLDPRT")).write_bytes(raw)
    revision = check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = check_output(["git", "rev-parse", "HEAD:src"], cwd=ROOT, text=True).strip()
    report = {"schema": "kit.sw2026.thin-revolve-generated-discovery.v1", "model_spec_sha256": digest(spec_raw),
              "prewriter_lock_sha256": LOCK_SHA256, "prewriter_lock_revision": PREWRITER_LOCK,
              "writer_revision": revision, "writer_sdk_tree": tree, "logical_candidate_directory": str(guest), "epoch": epoch,
              "tools": {name: digest((HERE / name).read_bytes()) for name in ("BuildThinControls.py", "ThinConstruct.py", "ThinNeutral.py")},
              "rows": {name: row for name, _, row in candidates}, "public_writer": False, "native_acceptance": False}
    (output / "BuildReceipt.json").write_bytes(encode(report))
    print(f"{len(candidates)} generated typed thin candidates, native acceptance pending")


def main():
    parser = ArgumentParser(description="Build guarded model-only disclosed cold thin revolve candidates")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest", type=PureWindowsPath)
    parser.add_argument("--epoch", type=int, default=1760000000)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker(json.load(sys.stdin))))
    else:
        require(args.spec and args.output and args.guest, "supply the disclosed spec and output locators")
        build(args.spec, args.output, args.guest, args.epoch)


if __name__ == "__main__":
    main()
