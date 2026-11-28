from __future__ import annotations

import argparse
import ast
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


SCHEMA = "kit.sw2026.authored-folder-order-process-job.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def checked(path, expected):
    data = Path(path).read_bytes()
    require(digest(data) == expected, "folder-order process input changed: " + str(path))
    return data


def verify_sources(job):
    source = json.loads(checked(job["writer_manifest"], job["writer_manifest_sha256"]))
    root = Path(job["writer_root"])
    require(len(source["files"]) == 3685, "folder-order source closure is incomplete")
    for name, expected in source["files"].items():
        checked(root / name, expected)


def recipe_order(data):
    module = ast.parse(data)
    function, = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "MakePartInput"]
    returned, = [node.value for node in function.body if isinstance(node, ast.Return)]

    def field(node, key):
        value, = [value for name, value in zip(node.keys, node.values, strict=True) if isinstance(name, ast.Constant) and name.value == key]
        return value

    folders = field(field(returned, "presentation"), "folder_names")
    return [ast.literal_eval(key) for key in folders.keys]


def build(job, request):
    root = Path(job["writer_root"])
    return subprocess.run([sys.executable, "-B", str(root / "re/tooling/sw2026/DrawingFrontBundleProcess.py")],
                          cwd=root, input=encoded(request), capture_output=True, timeout=90)


def successful_pair(job, request):
    first, second = (build(job, request) for _ in range(2))
    require(first.returncode == second.returncode == 0, "guarded folder-order construction failed")
    require(first.stdout == second.stdout and not first.stderr and not second.stderr, "folder-order builds differ")
    report = json.loads(first.stdout)
    require(report["input_runtime_file_access_attempts"] == 0 and report["inspection"]["readback_exact"],
            "folder-order process guard or typed readback failed")
    for kind in ("drawing", "part"):
        item = report[kind]
        data = b64decode(item.pop("artifact_base64"), validate=True)
        require(len(data) == item["bytes"] and digest(data) == item["sha256"], "folder-order artifact custody failed")
    return report


def run(job, job_sha):
    require(job["schema"] == SCHEMA, "folder-order process job schema differs")
    verify_sources(job)
    order = recipe_order(checked(job["recipe_path"], job["recipe_sha256"]))
    rows = []
    for case in job["default_cases"]:
        request = json.loads(checked(case["request"], case["request_sha256"]))
        require("folder_order" not in request["part"]["presentation"], "default probe contains an explicit order")
        expected = json.loads(checked(case["report"], case["report_sha256"]))
        actual = successful_pair(job, request)
        require(actual == expected, "existing default output changed: " + case["name"])
        rows.append({"name": case["name"], "complete_report_identical": True,
                     "drawing_sha256": actual["drawing"]["sha256"], "part_sha256": actual["part"]["sha256"]})
    request = json.loads(checked(job["ordered_request"], job["ordered_request_sha256"]))
    require(request["part"]["presentation"]["folder_order"] == order,
            "explicit folder order differs from the independent original recipe")
    ordered = successful_pair(job, request)
    expected = json.loads(checked(job["ordered_report"], job["ordered_report_sha256"]))
    require(ordered == expected, "frozen ordered output changed")
    invalid = [order[:-1], order + [order[0]], [order[0]] * len(order), ["moUnknownFolder_c", *order[1:]],
               [0, *order[1:]], ",".join(order), {"classes": order}]
    rejected = []
    for value in invalid:
        candidate = deepcopy(request)
        candidate["part"]["presentation"]["folder_order"] = value
        result = build(job, candidate)
        require(result.returncode != 0 and not result.stdout
                and b"authored part folder order must be an exact permutation" in result.stderr,
                "an invalid folder-order request crossed the process boundary")
        rejected.append({"input_kind": type(value).__name__, "rejected": True, "output_bytes": 0})
    verify_sources(job)
    return {"schema": "kit.sw2026.authored-folder-order-process-result.v1", "job_sha256": job_sha,
            "default_cases": rows, "all_default_artifacts_identical": True,
            "ordered_artifacts": {kind: ordered[kind]["sha256"] for kind in ("drawing", "part")},
            "ordered_source": "original MakePartInput AST key sequence", "invalid_requests": rejected,
            "guarded_successful_builds": 2 * (len(rows) + 1), "fresh_processes": 2 * (len(rows) + 1) + len(rejected),
            "runtime_input_file_access_attempts": 0, "native_acceptance": False, "heldout_inputs_read": 0,
            "vendor_runtime_executed": False, "source_closure_immutable": True, "passed": True}


def main():
    parser = argparse.ArgumentParser(description="Check authored part folder order across guarded writer processes")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    require(not arguments.output.exists(), "choose an unused folder-order process receipt path")
    result = run(json.loads(checked(arguments.job, arguments.job_sha256)), arguments.job_sha256)
    arguments.output.write_bytes(encoded(result))
    print(json.dumps({"passed": result["passed"], "output": str(arguments.output),
                      "sha256": digest(arguments.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
