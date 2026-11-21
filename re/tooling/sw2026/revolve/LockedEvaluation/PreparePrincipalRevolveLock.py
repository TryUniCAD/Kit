from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from secrets import randbelow
import json
import os
import re


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"


def case(name, split, plane, radius, axial, axis, angle, edit, reverse=False):
    return {
        "name": name,
        "split": split,
        "plane": plane,
        "radius_m": list(radius),
        "axial_m": list(axial),
        "axis_x_m": axis,
        "axis_axial_m": [axial[0] - 0.005, axial[1] + 0.007],
        "angle_deg": angle,
        "edit_angle_deg": edit,
        "reverse": reverse,
    }


def specifications():
    right = case(
        "PrincipalRevolveHeldoutRight", "heldout", "right",
        ((915 + randbelow(153)) / 100000, (2695 + randbelow(231)) / 100000),
        (-(683 + randbelow(139)) / 100000, (1460 + randbelow(273)) / 100000),
        (458 + randbelow(163)) / 100000, 48 + randbelow(32), 124 + randbelow(22),
    )
    top = case(
        "PrincipalRevolveHeldoutTop", "heldout", "top",
        ((1672 + randbelow(193)) / 100000, (3725 + randbelow(262)) / 100000),
        (-(1335 + randbelow(205)) / 100000, (901 + randbelow(271)) / 100000),
        -(516 + randbelow(133)) / 100000, 166 + randbelow(36), 236 + randbelow(28),
        reverse=True,
    )
    return {
        "schema": "kit.sw2026.ordinary-revolve-specs.v1",
        "cases": [
            case("PrincipalRevolveFrontFull", "discovery", "front", (0.007, 0.021),
                 (-0.008, 0.017), 0.002, 360, 153),
            case("PrincipalRevolveTopForward", "discovery", "top", (0.012, 0.029),
                 (-0.011, 0.016), 0.004, 104, 171),
            case("PrincipalRevolveTopReverse", "discovery", "top", (0.012, 0.029),
                 (-0.011, 0.016), 0.004, 104, 171, reverse=True),
            right, top,
        ],
    }


def publish(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return sha256(raw).hexdigest()


def prepare(args):
    if os.name != "nt" or not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
        raise ValueError("prepare the source specification inside the native oracle guest")
    work = args.workspace.resolve()
    checkout = args.checkout.resolve(strict=True)
    control = args.control.resolve(strict=True)
    if (
        work.drive.startswith("\\")
        or work.is_relative_to(checkout)
        or not work.parent.is_dir()
        or work.exists()
        or sha256(control.read_bytes()).hexdigest() != CONTROL
    ):
        raise ValueError("use an unused private guest directory and the measured control")
    work.mkdir()
    spec = work / "Specs.json"
    spec_sha = publish(spec, specifications())
    job = work / "Job.json"
    job_sha = publish(job, {
        "schema": "kit.sw2026.ordinary-revolve-job.v1",
        "source_revision": args.source_revision,
        "specs": str(spec),
        "specs_sha256": spec_sha,
        "control": str(control),
        "control_sha256": CONTROL,
        "checkout_root": str(checkout),
        "output": str(work / "Sources"),
        "oracle_sha256": ORACLE,
    })
    return {"job": str(job), "job_sha256": job_sha, "specs_sha256": spec_sha,
            "private_intents_disclosed": 0, "native_processes_started": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))
