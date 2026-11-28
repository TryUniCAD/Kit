from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    if arguments.output.exists():
        raise ValueError("choose an unused replay output directory")
    arguments.output.mkdir(parents=True)
    sys.path[:0] = [str(root), str(root / "src")]
    from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.CornerRequest import CornerRequest

    def write(name, value):
        path = arguments.output / name
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
        return sha256(path.read_bytes()).hexdigest()

    def phase(script, request, name):
        result = subprocess.run((sys.executable, "-I", "-B", str(root / "re/tooling/sw2026" / script), str(root)),
                                input=json.dumps(request, allow_nan=False), capture_output=True, text=True,
                                cwd=root, timeout=120, check=False)
        if result.returncode:
            raise ValueError(name + " failed: " + result.stderr + result.stdout)
        report = json.loads(result.stdout)
        if not report["passed"] or report["runtime_input_file_reads"] != 0 or report["native_acceptance"] or report["public_writer_qualified"]:
            raise ValueError(name + " violated guarded evidence scope")
        return report, write(name + ".json", report)

    outcomes = []
    for label, length, width, depth, variant in (
            ("OriginSyntheticAlpha", 31.75, 18.125, 9.625, False),
            ("OriginSyntheticBeta", 14.375, 27.625, 6.875, True),
            ("F14aSizedDiscovery", 20.0, 30.0, 10.0, False)):
        request = CornerRequest(label, length, width, depth, variant)
        request_sha = write(label + "Request.json", request)
        built, build_sha = phase("SdkCornerProcess.py", request, label + "Build")
        repeated, repeat_sha = phase("SdkCornerProcess.py", request, label + "Repeat")
        if built != repeated:
            raise ValueError("independent deterministic builds differ: " + label)
        packet = {"request": request, "build": built}
        prepared, prepare_sha = phase("SdkCornerPrepare.py", packet, label + "Prepare")
        compared, compare_sha = phase("SdkCornerCounterpart.py", packet, label + "Counterpart")
        blob = b64decode(built["blob"], validate=True)
        if sha256(blob).hexdigest() != built["sha256"]:
            raise ValueError("candidate custody differs")
        (arguments.output / (label + ".SLDPRT")).write_bytes(blob)
        outcomes.append({"name": label, "dimensions_mm": [length, width, depth], "candidate_sha256": built["sha256"],
                         "candidate_bytes": built["bytes"], "request_sha256": request_sha, "build_sha256": build_sha,
                         "repeat_sha256": repeat_sha, "prepare_sha256": prepare_sha, "counterpart_sha256": compare_sha,
                         "logical_streams_compared": len(compared["streams"]), "rejections_per_build": len(built["rejections"]),
                         "runtime_input_file_reads": 0, "deterministic": True, "anchor": prepared["anchor"]})
    result = {"schema": "kit.sw2026.sdk-corner-process-replay.v1", "passed": True,
              "processes": 12, "designs": outcomes, "native_acceptance": False, "public_writer_qualified": False,
              "fcstd_conversion_accepted": False, "heldout_inputs_read": 0}
    digest = write("Result.json", result)
    print(json.dumps({"passed": True, "result": str(arguments.output / "Result.json"), "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
