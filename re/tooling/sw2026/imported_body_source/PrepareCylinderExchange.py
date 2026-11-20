from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from AuthorCurves import require
from AuthorRectangleAnchors import CONTROL, ORACLE
from LocalBodyEnvelope import LOCAL, decode
from ObserveCylinderExchange import (
    BUILD_RECEIPT,
    GENERATED,
    NATIVE_RECEIPT,
    PHASES,
    SCHEMA,
    STOCK,
    TOLERANCES,
    TOOL_NAMES,
    checked,
    guest_directory,
    known_cases,
    raw_bytes,
    source_receipt,
)
from RunImportedBodySources import VERSION
from convert.adapters.solidworks.Container.Container import SldprtArchive

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def fingerprint(data):
    return sha256(data).hexdigest()


def write_exclusive(path, data):
    with path.open("xb") as stream:
        stream.write(data)
    checked(path, fingerprint(data), len(data))


def freeze_controls(source):
    receipt = checked(source / "Result.json", NATIVE_RECEIPT)
    source_receipt(receipt)
    files = {
        "Control.SLDPRT": checked(source / "Control.SLDPRT", CONTROL),
        "NativeSources.json": receipt,
    }
    case_names = {"CylinderZ": "StockZ", "CylinderReverseY": "StockReverseY"}
    for name, (source_hash, body_hash) in STOCK.items():
        source_name = name + ".SLDPRT"
        part = checked(source / source_name, source_hash)
        archive = SldprtArchive.from_bytes(part)
        envelope = decode(archive.require(LOCAL))
        require(
            envelope.storage_key == "Imported1"
            and len(envelope.kernel_stream) == 3525
            and fingerprint(envelope.kernel_stream) == body_hash,
            f"stock raw control changed: {name}",
        )
        files[source_name] = part
        files[case_names[name] + ".x_b"] = envelope.kernel_stream
    return files


def freeze_tools():
    sources = {}
    for name in sorted(TOOL_NAMES):
        path = HERE / name
        if not path.is_file():
            path = HERE.parent / name
        sources[name] = raw_bytes(path)
    return sources


def generated_body_files():
    with TemporaryDirectory(prefix="kit-cylinder-exchange-") as scratch:
        raw_directory = Path(scratch) / "Generated"
        python_path = os.pathsep.join(
            map(str, (ROOT / "src", ROOT, HERE.parent, HERE.parent / "serial"))
        )
        env = os.environ | {"PYTHONPATH": python_path}
        command = [sys.executable, "-B", str(HERE / "BuildLocalCylinder.py")]
        baseline = subprocess.check_output(command, cwd=ROOT, env=env)
        require(
            fingerprint(baseline) == BUILD_RECEIPT,
            "guarded cylinder build receipt changed",
        )
        emitted = subprocess.check_output(
            [*command, "--artifacts", str(raw_directory)], cwd=ROOT, env=env
        )
        require(
            emitted == baseline,
            "guarded cylinder build and exclusive artifact runs differ",
        )
        builds = json.loads(baseline)
        require(
            builds["construction_runtime_reads"]
            == builds["native_writer_outputs"]
            == builds["heldout_cases"]
            == 0
            and builds["native_loadability"] == "pending"
            and set(builds["cases"]) == GENERATED.keys(),
            "bare cylinder host evidence scope changed",
        )
        files = {"Build.json": baseline}
        for name, identity in GENERATED.items():
            raw_name = name + ".x_b"
            build = builds["cases"][name]
            require(
                build["raw"] == {"bytes": 1414, "sha256": identity}
                and build["typed_replay_exact"] is True,
                f"generated bare cylinder bytes changed: {name}",
            )
            target = known_cases()[name]["model"]
            source = build["input"]
            require(
                target
                == {
                    "face_center_m": tuple(
                        value / 1000.0 for value in source["start_mm"]
                    ),
                    "axis": tuple(source["axis"]),
                    "radius_m": source["radius_mm"] / 1000.0,
                    "height_m": source["height_mm"] / 1000.0,
                },
                f"independent native expectation differs from the guarded model: {name}",
            )
            files[raw_name] = checked(raw_directory / raw_name, identity, 1414)
    return files


def stage(destination, guest, source):
    target = destination.resolve()
    require(
        not destination.is_symlink()
        and not target.exists()
        and not target.is_relative_to(ROOT),
        "use an unused cylinder packet destination outside Kit",
    )
    native_destination = str(guest_directory(guest))
    control_files = freeze_controls(source.resolve(strict=True))
    tools = freeze_tools()
    candidates = generated_body_files()
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    job = {
        "schema": SCHEMA,
        "oracle_version": VERSION,
        "oracle_sha256": ORACLE,
        "tool_checkout_head": head,
        "guest_directory": native_destination,
        "control_sha256": CONTROL,
        "build_sha256": BUILD_RECEIPT,
        "source_receipt_sha256": NATIVE_RECEIPT,
        "phases": PHASES,
        "tolerances": TOLERANCES,
        "tools_sha256": {name: fingerprint(content) for name, content in tools.items()},
        "cases": known_cases(),
    }
    target.mkdir()
    tool_directory = target / "Tools"
    tool_directory.mkdir()
    for name, content in tools.items():
        write_exclusive(tool_directory / name, content)
    for name, content in (control_files | candidates).items():
        write_exclusive(target / name, content)
    data = (json.dumps(job, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    identity = fingerprint(data)
    job_path = target / "Job.json"
    write_exclusive(job_path, data)
    verified = subprocess.check_output(
        [
            sys.executable,
            "-B",
            "-E",
            "-S",
            str(tool_directory / "ObserveCylinderExchange.py"),
            str(job_path),
            "--job-sha256",
            identity,
            "--verify-only",
        ],
        cwd=target,
        text=True,
    )
    require(
        json.loads(verified)
        == {"verified": True, "job_sha256": identity, "native_processes": 0},
        "standalone cylinder oracle packet failed host verification",
    )
    return {
        "job_sha256": identity,
        "packet": str(target),
        "guest_directory": native_destination,
        "verified": True,
        "native_processes": 0,
    }


def main():
    parser = ArgumentParser(
        description="Stage two verified generated cylinders and separate stock native controls"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("guest_directory")
    parser.add_argument("--stock-packet", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            json.dumps(stage(args.destination, args.guest_directory, args.stock_packet))
        )
        return 0
    except Exception as error:
        print(json.dumps({"stage": "refused", "failure": repr(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
