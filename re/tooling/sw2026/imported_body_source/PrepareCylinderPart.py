from argparse import ArgumentParser
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from AuthorCurves import require
from AuthorRectangleAnchors import CONTROL, ORACLE
from ObserveCylinderExchange import (
    NATIVE_RECEIPT,
    STOCK,
    TOLERANCES,
    checked,
    raw_bytes,
    source_receipt,
)
from ObserveLocalCylinderPart import (
    BUILD_HASH,
    CONTROL_FILES,
    EXCHANGE_HASH,
    GUEST_ROOT,
    PARTS,
    PHASES,
    PLANAR_BUILD_HASH,
    PLANAR_HASH,
    PLANAR_NAME,
    PLANAR_NATIVE_HASH,
    SCHEMA,
    TOOLS,
    exchange_evidence,
    planar_case,
    verify_build,
)
from PrepareCylinderExchange import fingerprint, write_exclusive
from RunImportedBodySources import VERSION

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def lock_controls(stock, planar, exchange):
    files = {
        "Control.SLDPRT": checked(stock / "Control.SLDPRT", CONTROL),
        PLANAR_NAME: checked(planar / "Candidates" / PLANAR_NAME, PLANAR_HASH, 9914),
        "NativeSources.json": checked(stock / "Result.json", NATIVE_RECEIPT),
        "NativeExchange.json": checked(exchange, EXCHANGE_HASH),
        "PlanarBuild.json": checked(planar / "Build.json", PLANAR_BUILD_HASH),
        "PlanarNative.json": checked(planar / "Result.json", PLANAR_NATIVE_HASH),
    }
    for name, identity in STOCK.items():
        filename = name + ".SLDPRT"
        files[filename] = checked(stock / filename, identity[0])
    source_receipt(files["NativeSources.json"])
    exchange_evidence(files["NativeExchange.json"])
    planar_case(files["PlanarBuild.json"], files["PlanarNative.json"])
    return files


def lock_tools():
    tools = {}
    for name in sorted(TOOLS):
        source = HERE / name
        if not source.is_file():
            source = HERE.parent / name
        tools[name] = raw_bytes(source)
    return tools


def build_parts():
    python_path = os.pathsep.join(
        map(str, (ROOT / "src", ROOT, HERE.parent, HERE.parent / "serial"))
    )
    env = os.environ | {"PYTHONPATH": python_path}
    command = [
        sys.executable,
        "-B",
        str(HERE / "BuildLocalCylinderPart.py"),
        GUEST_ROOT,
    ]
    with TemporaryDirectory(prefix="kit-embedded-cylinder-build-") as scratch:
        artifacts = Path(scratch) / "Candidates"
        first = subprocess.check_output(command, cwd=ROOT, env=env)
        second = subprocess.check_output(
            [*command, "--artifacts", str(artifacts)], cwd=ROOT, env=env
        )
        require(
            first == second and fingerprint(first) == BUILD_HASH,
            "the guarded part proof or its frozen build identity changed",
        )
        verify_build(first)
        files = {
            name
            + ".SLDPRT": checked(
                artifacts / (name + ".SLDPRT"), identity["sha256"], identity["bytes"]
            )
            for name, identity in PARTS.items()
        }
    return first, files


def stage(destination, stock, planar, exchange):
    target = destination.resolve()
    require(
        not destination.is_symlink()
        and not target.exists()
        and not target.is_relative_to(ROOT),
        "use an unused embedded cylinder packet directory outside Kit",
    )
    controls = lock_controls(
        stock.resolve(strict=True), planar.resolve(strict=True), exchange
    )
    tools = lock_tools()
    controls["Build.json"], files = build_parts()
    require(
        set(controls) == CONTROL_FILES.keys(),
        "embedded cylinder control inventory changed",
    )
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    job = {
        "schema": SCHEMA,
        "oracle_version": VERSION,
        "oracle_sha256": ORACLE,
        "guest_root": GUEST_ROOT,
        "tool_checkout_head": head,
        "control_files": CONTROL_FILES,
        "phases": PHASES,
        "tolerances": TOLERANCES,
        "tools_sha256": {name: fingerprint(data) for name, data in tools.items()},
        "cases": PARTS,
    }
    target.mkdir()
    tools_dir, candidate_dir = target / "Tools", target / "Candidates"
    tools_dir.mkdir()
    candidate_dir.mkdir()
    for directory, items in (
        (target, controls),
        (tools_dir, tools),
        (candidate_dir, files),
    ):
        for name, data in items.items():
            write_exclusive(directory / name, data)
    data = (json.dumps(job, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    identity = fingerprint(data)
    path = target / "Job.json"
    write_exclusive(path, data)
    proof = subprocess.check_output(
        [
            sys.executable,
            "-B",
            "-E",
            "-S",
            str(tools_dir / "ObserveLocalCylinderPart.py"),
            str(path),
            "--job-sha256",
            identity,
            "--verify-only",
        ],
        cwd=target,
        text=True,
    )
    require(
        json.loads(proof)
        == {"verified": True, "job_sha256": identity, "native_processes": 0},
        "standalone embedded cylinder packet custody did not verify",
    )
    return {
        "job_sha256": identity,
        "packet": str(target),
        "guest_root": GUEST_ROOT,
        "native_processes": 0,
        "verified": True,
    }


def main():
    parser = ArgumentParser(
        description="Stage the frozen embedded cylinder part lifecycle and its native controls"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("--stock-packet", required=True, type=Path)
    parser.add_argument("--planar-packet", required=True, type=Path)
    parser.add_argument("--exchange-receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                stage(
                    args.destination,
                    args.stock_packet,
                    args.planar_packet,
                    args.exchange_receipt,
                )
            )
        )
        return 0
    except Exception as error:
        print(json.dumps({"stage": "refused", "failure": repr(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
