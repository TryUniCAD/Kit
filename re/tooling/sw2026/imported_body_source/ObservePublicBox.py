from argparse import ArgumentParser
from itertools import product
import json
from math import prod
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ObservePublicCyl import (
    CONTROL, IMPORT, ORACLE, REPO, RESEARCH, digest, file_bytes, measure_lifecycle,
    publish, require, tracked_extract,
)


HERE = Path(__file__).resolve()
GUEST = r"C:\KitPublicBox01"
NAME = "TranslatedBox.SLDPRT"
CONFIGURATION = "Inspection"
SCHEMA = "kit.sw2026.rectangular-import-public-native.v1"
BOUNDS_MM = ((-19.25, 2.375), (5.125, 36.75), (-12.25, 4.875))
BOUNDS_SI = {"bounds_m": [[value * 0.001 for value in axis] for axis in BOUNDS_MM]}
EXTRA = (f"{IMPORT}/{HERE.name}", f"{IMPORT}/VerifyPublicBox.py", "attached_top_box_source/BoxIncidence.py")


def profile():
    return {
        "schema": SCHEMA,
        "oracle_version": "34.5.2.0604",
        "oracle_sha256": ORACLE,
        "guest": GUEST,
        "configuration": CONFIGURATION,
        "authored_boundary_si": BOUNDS_SI,
        "control_sha256": CONTROL,
    }


def freeze(destination, revision, control):
    require(re.fullmatch(r"[0-9a-f]{40}", revision) and not destination.exists()
            and not destination.resolve().is_relative_to(REPO), "use an unused external packet")
    seed = file_bytes(control, CONTROL)
    destination.mkdir()
    code = destination / "Kit"
    code.mkdir()
    with TemporaryDirectory(prefix="kit-public-box-boundary-") as scratch:
        tracked_extract(revision, code, Path(scratch) / "Files.tar", extra=EXTRA)
    require((code / RESEARCH / EXTRA[0]).read_bytes() == HERE.read_bytes(),
            "observer matches a different Git revision")
    publish(destination / "Control.SLDPRT", seed)
    inventory = {path.relative_to(code).as_posix(): digest(path.read_bytes())
                 for path in sorted(code.rglob("*")) if path.is_file()}
    require(len(inventory) > 5000, "incomplete tracked SDK closure")
    job = profile() | {"revision": revision, "file_inventory": inventory}
    return {"job_sha256": publish(destination / "Job.json", job), "revision": revision,
            "code_files": len(inventory), "native_processes": 0}


def verify(job_path, checksum):
    job = json.loads(file_bytes(job_path, checksum))
    packet = job_path.parent.resolve()
    code = packet / "Kit"
    require(job_path.name == "Job.json" and HERE == (code / RESEARCH / EXTRA[0]).resolve()
            and all(job[key] == value for key, value in profile().items())
            and re.fullmatch(r"[0-9a-f]{40}", job["revision"]),
            "locked rectangular profile does not match this observer")
    require(len(job["file_inventory"]) > 5000, "incomplete tracked SDK closure")
    for relative, identity in job["file_inventory"].items():
        path = code / relative
        require(path.resolve().is_relative_to(code), "code escaped its packet")
        file_bytes(path, identity)
    file_bytes(packet / "Control.SLDPRT", CONTROL)
    sys.path[:0] = [str(code / relative) for relative in (
        f"{RESEARCH}/{IMPORT}", RESEARCH, f"{RESEARCH}/serial", "src", "",
    )]
    return packet, job


def build(packet, checksum):
    from VerifyPublicBox import (
        CAPS, EMITTER, STAGED_BOUNDS, box_document, check_target, fingerprint,
        guard_build, guarded_prepare, observed_box, warm, write_document,
    )
    require(os.name == "nt" and STAGED_BOUNDS == BOUNDS_MM, "run the exact model in the Windows guest")
    target = Path(GUEST) / "Candidate" / NAME
    require(not target.parents[1].exists() and not (packet / "Build.json").exists(),
            "choose the unused native candidate locator")
    warm()
    document = box_document(BOUNDS_MM, CONFIGURATION)
    with patch(EMITTER + ".PrepareNative", side_effect=guarded_prepare) as prepare:
        result = write_document(document, target, allow_carrier=False)
    require(prepare.call_count == 1 and result.path == target
            and result.native_capabilities == result.transferred_capabilities == CAPS
            and len(result.transfers) == 2 and not (result.dropped or result.requirements),
            "normal staged writer changed its geometry-only request")
    data = target.read_bytes()
    check_target(target, data)
    with guard_build():
        geometry = observed_box(data, BOUNDS_MM, CONFIGURATION, str(target))
    exact = fingerprint(data)
    proof = {"part": exact, "native_caps": sorted(item.value for item in CAPS),
             "writer_epoch": prepare.call_args.args[2], "strict_geometry": geometry,
             "runtime_input_reads": 0, "native_processes_started": 0}
    lock = {"job_sha256": checksum, "destination": str(target), "result": {"windows_disclosed": proof}}
    return {"build_sha256": publish(packet / "Build.json", lock), "candidate": exact}


def measure(packet, job, checksum, build_hash):
    from ObserveKernelBodyRestore import measure_body

    def measure_box(observer, body, expected, *, temporary):
        return measure_body(observer, body, expected, temporary=temporary)

    bounds = BOUNDS_SI["bounds_m"]
    width, height, depth = (high - low for low, high in bounds)
    expected = {
        "faces": 6, "edges": 12, "vertices": 8, "corners_m": tuple(product(*bounds)),
        "volume_m3": prod((width, height, depth)),
        "area_m2": 2 * (width * height + height * depth + width * depth),
        "com_m": tuple((low + high) / 2 for low, high in bounds),
    }
    return measure_lifecycle(packet, job, checksum, build_hash, Path(GUEST), NAME, measure_box, expected)


def main():
    parser = ArgumentParser(description="Verify a normal Windows path write of a rectangular imported body")
    modes = parser.add_subparsers(dest="mode", required=True)
    first = modes.add_parser("freeze")
    first.add_argument("destination", type=Path)
    first.add_argument("revision")
    first.add_argument("control", type=Path)
    for mode in ("build", "measure"):
        current = modes.add_parser(mode)
        current.add_argument("job", type=Path)
        current.add_argument("job_sha256")
        if mode == "measure":
            current.add_argument("build_sha256")
    args = parser.parse_args()
    if args.mode == "freeze":
        result = freeze(args.destination, args.revision, args.control)
    else:
        packet, job = verify(args.job, args.job_sha256)
        result = (build(packet, args.job_sha256) if args.mode == "build"
                  else measure(packet, job, args.job_sha256, args.build_sha256))
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("passed", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
