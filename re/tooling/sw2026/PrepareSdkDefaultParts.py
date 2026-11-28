from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from time import time

from AuthorCurves import digest, require
from AuthorRectangleAnchors import CONTROL, ORACLE
from InspectSdkDefaultParts import SCHEMA, TOOLS
from PrepareSdkPolygonCohort import prism


DESIGNS = (
    ("Skew", "sdk factory skew", ((-14.2, -3.8), (24.9, 1.7), (4.1, 29.5))),
    ("Step", "sdk 設計 stepped", ((-13.1, -10.2), (28.4, -10.2), (28.4, 23.7), (6.7, 23.7), (6.7, 6.4), (-13.1, 6.4))),
)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write(path, raw):
    with path.open("xb") as file:
        file.write(raw)
    return sha256(raw).hexdigest()


def neutral(role, name, vertices, output, written):
    from interchange.serialization.Deserialize import FromData
    from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase

    authored = MakePolygonCase(name, vertices, role == "Step")
    document = FromData(authored["document"])
    sketch = document.sketches[0]
    feature = document.feature_timeline[0]
    depth = document.parameters[0].value.value / 1000
    edited = depth + (0.004137 if role == "Skew" else 0.006251)
    filename = name + ".SLDPRT"
    locator = str(PureWindowsPath(r"C:\KitSdkCandidates", filename))
    request = {"document": authored["document"], "written_at": written,
               "destination": str(output / filename), "expected_locator": locator}
    presentation = authored["settings"]["system"]
    presentation["folders"] = [[tag, "Lights and Cameras" if tag == "moEnvFolder_c" else label]
                               for tag, label in presentation["folders"]]
    expected = {"intent": {"self_path": locator, "model_name": name, "configuration_name": document.configurations[0].name,
                           "profile": sketch.name, "feature": feature.name, "support": "Front Plane",
                           "resolved_roots": 19, "sketch_lines": len(vertices), "fixed_relations_in_user_sketch": 0,
                           "vertices_m": [[x / 1000, y / 1000] for x, y in vertices], "depth_m": depth},
                "expected_initial": prism(vertices, depth),
                "edit": {"dimension": "D1@" + feature.name, "new_depth_m": edited, "expected": prism(vertices, edited)},
                "native_presentation": {"settings": {"system": presentation}}}
    return request, expected, filename


def launch(source, payload):
    return subprocess.run([sys.executable, "-I", "-B", str(source / "re/tooling/sw2026/SdkNeutralPartProcess.py"), str(source)],
                          cwd=source, input=payload, capture_output=True, timeout=120)


def prepare(args):
    source = args.code.resolve(strict=True)
    manifest = source.parent / "FrozenSource.json"
    require(digest(manifest) == args.source_sha256, "wrong default-part SDK source closure")
    for name, expected in json.loads(manifest.read_bytes())["files_sha256"].items():
        require(digest(source / name) == expected, "a frozen default-part SDK dependency changed")
    out = args.output.resolve()
    out.mkdir()
    sys.path[:0] = [str(source), str(source / "src")]
    written = int(time())
    summary = {"schema": SCHEMA, "frozen_source_sha256": args.source_sha256, "written_at": written,
               "cases": [], "runtime_reads": 0, "heldout_inputs_read": 0, "passed": False}
    for role, name, vertices in DESIGNS:
        dest = out / role
        dest.mkdir()
        request, expected, filename = neutral(role, name, vertices, dest, written)
        payload = encode(request)
        request_sha = write(dest / "SdkRequest.json", payload)
        expected_sha = write(dest / "Expected.json", encode(expected))
        results = []
        for series in ("A", "B"):
            result = launch(source, payload)
            data_sha = write(dest / (series + ".stdout"), result.stdout)
            write(dest / (series + ".stderr"), result.stderr)
            require(result.returncode == 0 and not result.stderr, "the guarded default SDK writer failed")
            results.append((json.loads(result.stdout), data_sha))
        require(results[0] == results[1], "default part reconstruction differs across guarded processes")
        row, row_sha = results[0]
        require(row["passed"] and row["runtime_reads"] == 0 and not row["native_acceptance"],
                "guarded default-part output has unproven state")
        raw = b64decode(row["blob"], validate=True)
        candidate_sha = write(dest / filename, raw)
        require(candidate_sha == row["sha256"] and len(raw) == row["bytes"], "the generated part bytes changed")
        summary["cases"].append({"role": role, "request_sha256": request_sha, "expected_sha256": expected_sha,
                                 "build_a_sha256": row_sha, "build_b_sha256": row_sha, "candidate_sha256": candidate_sha,
                                 "bytes": len(raw), "streams": row["streams"]})
    require(summary["cases"][0]["bytes"] != summary["cases"][1]["bytes"], "parts did not vary with the neutral design")
    summary["passed"] = True
    proof = write(out / "BuildProof.json", encode(summary))
    require(write(out / "Control.SLDPRT", args.control.read_bytes()) == CONTROL, "wrong disclosed fixed control")
    tools = out / "Tools"
    tools.mkdir()
    tool_hashes = {name: write(tools / name, (source / "re/tooling/sw2026" / name).read_bytes()) for name in TOOLS}
    packet = {"schema": SCHEMA, "oracle_sha256": ORACLE, "build_proof_sha256": proof,
              "tools": tool_hashes, "heldout_inputs_read": 0}
    packet_sha = write(out / "Packet.json", encode(packet))
    print(json.dumps({"passed": True, "packet_sha256": packet_sha, "build_proof_sha256": proof,
                      "frozen_source_sha256": args.source_sha256, "workers": 4}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Freeze disclosed neutral-only SDK parts and oracle methods")
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
