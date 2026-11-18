from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from argparse import ArgumentParser
parser = ArgumentParser(description="Replay the frozen complete through-all process boundary with explicit research roots")
parser.add_argument("--preparation-root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
options = parser.parse_args()
base = options.preparation_root.resolve(strict=True)
output = options.output
output.mkdir(exist_ok=False)
code = base / "CodeRoot"
baseline = base / "Baseline01"
records = []
manifest = json.loads((base / "MethodSourceManifest02.json").read_bytes())
for relative, expected in manifest["source_files"].items():
    assert sha256((code / relative).read_bytes()).hexdigest() == expected["sha256"], relative
for relative, expected in manifest["inputs"].items():
    assert sha256((base / relative).read_bytes()).hexdigest() == expected["sha256"], relative


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run(label, program, root, args, request, passed=True):
    payload = json.dumps(request, sort_keys=True, allow_nan=False).encode()
    result = subprocess.run([sys.executable, "-B", str(program), str(root), *args], input=payload, capture_output=True, timeout=90)
    detail = {"label": label, "returncode": result.returncode, "input_sha256": sha256(payload).hexdigest(), "stdout_sha256": sha256(result.stdout).hexdigest(), "stderr_sha256": sha256(result.stderr).hexdigest(), "stderr": result.stderr.decode()}
    if result.returncode == 0:
        value = json.loads(result.stdout)
        assert value["passed"] and passed, (label, detail)
        write(output / label / "Record.json", {key: val for key, val in value.items() if key != "generated"})
    else:
        assert not passed and not result.stdout, (label, detail)
        value = None
    write(output / label / "Process.json", detail)
    records.append(detail)
    return value


def case_job(case):
    request = json.loads((base / "Inputs" / (case + ".json")).read_bytes())
    program = code / "re/tooling/sw2026/ThroughAllColdProcess.py"
    left = run(case + "BuildA", program, code, ["build"], request)
    right = run(case + "BuildB", program, code, ["build"], request)
    assert left == right, case
    audited = run(case + "Audit", program, code, ["audit"], {"recipe": request, "generated": left["generated"]})
    assert left["sha256"] == audited["sha256"]
    from base64 import b64decode
    data = b64decode(left["generated"], validate=True)
    artifact = output / "Generated" / (request["name"] + ".SLDPRT")
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_bytes(data)
    return {"case": case, "artifact_sha256": left["sha256"], "bytes": left["bytes"], "stream_comparisons": len(left["streams"]) * 3, "grammar": left["grammar"]}


with ThreadPoolExecutor(max_workers=3) as pool:
    positives = list(pool.map(case_job, ("G01", "G02", "G03")))

base_request = json.loads((base / "Inputs/G01.json").read_bytes())
faults = []
for label, mutate in (
    ("depth-owner", lambda value: value.update(cut_depth_m=0.004)),
    ("draft-owner", lambda value: value.update(draft_angle=0.0)),
    ("metadata-loss", lambda value: value.update(custom_properties={"hidden": "text"})),
    ("boss-operation", lambda value: value.update(operation="boss")),
    ("invalid-direction", lambda value: value.update(direction="up_to_body")),
    ("nonprincipal-plane", lambda value: value.update(axis="rotated")),
    ("wrong-destination", lambda value: value.update(native_path=r"C:\WrongName.SLDPRT")),
    ("outside-circle", lambda value: value.update(circle_center_m=[1.0, 1.0])),
    ("zero-stock-depth", lambda value: value.update(stock_size_m=[.08137, .05791, 0.0])),
    ("negative-radius", lambda value: value.update(radius_m=-.00713)),
):
    request = deepcopy(base_request)
    mutate(request)
    run("Reject-" + label, code / "re/tooling/sw2026/ThroughAllColdProcess.py", code, ["build"], request, False)
    faults.append(label)

comparisons = []
for mode in ("blind", "mid_plane", "two_directions"):
    before = run("Legacy-" + mode + "-Before", base / "LegacyEndColdProcess.py", baseline, [], {"mode": mode})
    after = run("Legacy-" + mode + "-After", base / "LegacyEndColdProcess.py", code, [], {"mode": mode})
    assert before == after, mode
    comparisons.append({"case": mode, "sha256": before["sha256"], "bytes": before["bytes"], "complete_output_unchanged": True})

for request_path in sorted((base / "LegacyPocketInputs").glob("*.Request.json")):
    request = json.loads(request_path.read_bytes())
    label = request_path.name.split(".")[0]
    values = []
    for name, tree in (("Before", baseline), ("After", code)):
        values.append(run("Legacy-" + label + "-" + name, tree / "re/tooling/sw2026/SdkPocketProcess.py", tree, ["build"], request))
    assert values[0] == values[1], label
    comparisons.append({"case": label, "sha256": values[0]["sha256"], "bytes": values[0]["bytes"], "complete_output_unchanged": True})

receipt = {"schema": "kit.sw2026.through-all-cold-process.v1", "passed": True, "native_acceptance": False, "public_writer_qualified": False, "heldout_payloads_read": 0, "workers": len(records), "positive_cases": positives, "negative_cases": faults, "legacy_equivalence": comparisons, "processes": sorted(records, key=lambda value: value["label"])}
write(output / "Result.json", receipt)
print(json.dumps({key: value for key, value in receipt.items() if key != "processes"}, indent=2, sort_keys=True))
