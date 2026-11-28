from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from os import name as os_name
from pathlib import Path
from subprocess import run
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveMeasuredPrincipalRevolve import ROOT, WriterAudit
from ProveMeasuredThinRevolve import sector_centroid
from ThinProofModel import neutral
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from interchange.document.Behavior.DocumentIo import ToJson

CASES = (
    {
        "name": "ThinQueueFront", "plane": "front", "reverse": False,
        "axis_x_m": 0.004, "axis_axial_m": [-0.013, 0.028],
        "axial_m": [-0.004, 0.018], "profile_radius_m": 0.021,
        "angle_deg": 113, "wall_mode": "two", "wall_m": [0.0017, 0.0029],
        "edit_angle_deg": 131, "edit_wall_m": [0.0022, 0.0036],
    },
    {
        "name": "ThinQueueRight", "plane": "right", "reverse": False,
        "axis_x_m": -0.006, "axis_axial_m": [-0.018, 0.026],
        "axial_m": [-0.009, 0.015], "profile_radius_m": 0.017,
        "angle_deg": 79, "wall_mode": "midplane", "wall_m": [0.0024, 0.0],
        "edit_angle_deg": 97, "edit_wall_m": [0.0031, 0.0],
    },
)


def digest(data):
    return sha256(data).hexdigest()


def expected(case):
    from math import radians
    radius = case["profile_radius_m"]
    first, second = case["wall_m"]
    if case["wall_mode"] == "midplane":
        inner, outer = radius - first / 2, radius + first / 2
        mode = "midplane"
    else:
        inner, outer = radius - second, radius + first
        mode = "two_sided"
    height = case["axial_m"][1] - case["axial_m"][0]
    return {
        "body_count": 1,
        "volume_m3": height * radians(case["angle_deg"]) * (outer * outer - inner * inner) / 2,
        "centroid_m": sector_centroid(case, mode),
        "angle_radians": radians(case["angle_deg"]),
        "wall_metres": case["wall_m"],
    }


def prepare(output):
    if os_name != "nt":
        raise ValueError("use Windows so candidate self locators name their actual native paths")
    output = output.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError("use a fresh absolute research output outside the checkout")
    revision = run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tree = run(["git", "rev-parse", "HEAD:src"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if run(["git", "diff", "--quiet", "HEAD", "--", "src"], cwd=ROOT).returncode:
        raise ValueError("candidate preparation requires an unchanged SDK source tree")
    models = []
    for case in CASES:
        for edited in (False, True):
            variant = dict(case)
            if edited:
                variant.update(angle_deg=case["edit_angle_deg"], wall_m=case["edit_wall_m"])
            name = case["name"] + ("Edited" if edited else "Original")
            variant["name"] = name
            document = neutral(variant)
            document.assert_valid()
            GetDocumentCaps(document)
            models.append((name, variant, document, output / "Candidates" / (name + ".SLDPRT")))
    for encoding in ("utf-8", "utf-16-le", "ascii"):
        lookup(encoding)
    audit = WriterAudit(output / "NoOutputDuringConstruction")
    candidates = []
    for name, case, document, target in models:
        payload = audit.run(lambda: PrepareRevolve(document, target, 1795893600)).BytesValue
        repeat = audit.run(lambda: PrepareRevolve(document, target, 1795893600)).BytesValue
        if payload != repeat:
            raise ValueError("model-only candidate changed on deterministic repetition")
        candidates.append((name, payload, document, case, target))
    runtime = audit.report()
    output.mkdir(parents=True, exist_ok=False)
    (output / "Candidates").mkdir()
    (output / "Models").mkdir()
    rows = []
    for name, payload, document, case, target in candidates:
        target.write_bytes(payload)
        model = ToJson(document, IndentSize=2).encode("utf-8")
        (output / "Models" / (name + ".json")).write_bytes(model)
        rows.append({"name": name, "candidate": str(target.relative_to(output)), "sha256": digest(payload),
                     "bytes": len(payload), "model_sha256": digest(model), "authored_case": case,
                     "analytic_expected": expected(case)})
    receipt = {
        "schema": "kit.sw2026.saved-thin-queue-preparation.v1",
        "task_id": "B08-PR247-SAVED-THIN-COVERAGE", "writer_revision": revision, "sdk_tree": tree,
        "tool_sha256": {name: digest(Path(__file__).with_name(name).read_bytes()) for name in
                        (Path(__file__).name, "ThinProofModel.py", "ProveMeasuredPrincipalRevolve.py", "ProveMeasuredThinRevolve.py")},
        "written_at": 1795893600,
        "runtime": runtime, "cases": rows, "native_run": "unrun", "vendor_loadable": False,
        "application_usable": False, "heldout_acceptance": False,
        "purpose": "native save captures for strict refusal, permissive inspection and raw extraction coverage",
        "native_requirements": ["healthy control before and after", "fresh candidate process",
                                "open without repair and rebuild", "measure bodies, volume, centroid and feature owners",
                                "edit actual angle and both active walls, restore and save to a new path",
                                "fresh reopen saved file and compare owners and geometry", "retain exact saved bytes and all receipts"],
        "publication_gate": "unchanged; these are unqualified research candidates only",
    }
    (output / "Preparation.json").write_text(dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(dumps({"candidates": len(rows), "native_run": "unrun", "runtime": runtime}, sort_keys=True))


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare source-free thin candidates for genuine native-save queue fixtures")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error("--output must be absolute")
    prepare(args.output)
