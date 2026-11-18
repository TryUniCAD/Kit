from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(root, expected):
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(root / "Tools" / "AuthorThroughAllSources.py"),
            "verify",
            str(root / "Source.json"),
            "--packet-sha256",
            expected,
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    parsed = json.loads(result.stdout)
    if result.stderr or parsed.get("native_processes_started", 0) != 0:
        raise ValueError("The packet verifier crossed its host-only boundary")
    return {"returncode": result.returncode, "result": parsed}


def replicate(root, output):
    output.mkdir()
    (output / "Tools").mkdir()
    job = json.loads((root / "Source.json").read_bytes())
    for name in job["tools_sha256"]:
        copyfile(root / "Tools" / name, output / "Tools" / name)
    for name in (
        "Source.json",
        "Control.SLDPRT",
        "Disclosed.json",
        "NativeBinding.json",
        "Custody.json",
    ):
        copyfile(root / name, output / name)


def main():
    parser = argparse.ArgumentParser(
        description="Check the real frozen source verifier across an isolated process boundary without importing COM or reading hidden designs"
    )
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if (
        packet.name != "Source.json"
        or digest(packet) != args.packet_sha256
        or args.output.exists()
    ):
        raise ValueError("Use the exact frozen packet and unused audit output")
    args.output.mkdir()
    results = {"positive": invoke(packet.parent, args.packet_sha256)}
    if results["positive"] != {
        "returncode": 0,
        "result": {
            "passed": True,
            "native_processes_started": 0,
            "new_heldout_inputs_read": 0,
        },
    }:
        raise ValueError("The genuine packet did not pass the actual source verifier")
    cases = (
        "wrong-packet-hash",
        "missing-control",
        "changed-disclosed",
        "changed-tool",
        "inherited-state-shadow",
        "noncanonical-prior-seal",
    )
    for name in cases:
        output = args.output / name
        replicate(packet.parent, output)
        expected = args.packet_sha256
        if name == "wrong-packet-hash":
            expected = "0" * 64
        elif name == "missing-control":
            (output / "Control.SLDPRT").unlink()
        elif name == "changed-disclosed":
            (output / "Disclosed.json").write_text("{}\n", encoding="utf-8")
        elif name == "changed-tool":
            target = output / "Tools" / "ThroughAllSourcePlan.py"
            target.write_bytes(target.read_bytes() + b"\n")
        else:
            job = json.loads((output / "Source.json").read_bytes())
            if name == "inherited-state-shadow":
                target = output / "Tools" / "ThroughAllAuthor.py"
                content = target.read_text().replace("owned_dimensions", "dimensions")
                target.write_text(content, encoding="utf-8")
                job["tools_sha256"][target.name] = digest(target)
            else:
                if job.get("sealed_source") is None:
                    raise ValueError(
                        "The retry audit requires a bound existing opaque source seal"
                    )
                job["sealed_source"]["windows_path"] += ".invalid"
            (output / "Source.json").write_text(
                json.dumps(job, indent=2) + "\n", encoding="utf-8"
            )
            expected = digest(output / "Source.json")
        results[name] = invoke(output, expected)
        if results[name] != {
            "returncode": 3,
            "result": {"passed": False, "stage": "preflight_failed"},
        }:
            raise ValueError(
                "A malformed packet was not rejected at the real verifier boundary"
            )
    result = {
        "schema": "kit.sw2026.through-all-packet-process-proof.v1",
        "packet_sha256": args.packet_sha256,
        "tool_sha256": digest(Path(__file__)),
        "python_version": sys.version,
        "workers": len(results),
        "results": results,
        "passed": True,
        "native_processes_started": 0,
        "new_heldout_inputs_read": 0,
        "writer_output_count": 0,
    }
    target = args.output / "Result.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": True,
                "workers": len(results),
                "sha256": digest(target),
                "native_processes_started": 0,
                "new_heldout_inputs_read": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
