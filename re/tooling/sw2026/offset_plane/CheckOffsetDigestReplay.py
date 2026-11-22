from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path
import platform
from subprocess import run
import sys
import zlib


ROOT = Path(__file__).resolve().parents[4]
RECEIPT_SHA = "79210ac088a95b3c6d0913b8a056e678e8dbe14e9a861f178455ea0426f6e80c"
D03_REQUEST_SHA = "4b435b0e6328626aac0d2b6bf65421c830e9a7f2f72474b7a7db1639d499c018"
WORKER = Path(__file__).with_name("CheckTypedOffset.py")


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected, base):
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(base.resolve(strict=True)):
        raise ValueError("checked path left its original root")
    data = resolved.read_bytes()
    if digest(data) != expected:
        raise ValueError("checked file digest differs")
    return data


def replay(request, expected):
    results = []
    for _ in range(2):
        process = run(
            (sys.executable, "-I", "-B", str(WORKER), "--worker", "--platform-views"),
            input=request,
            capture_output=True,
            timeout=150,
            cwd=ROOT,
        )
        if process.returncode:
            return {"passed": False, "failure_code": "worker_failed"}
        results.append(loads(process.stdout))
    first, second = results
    return {
        "passed": first == second
        and first["sha256"] == expected
        and first["runtime_input_file_reads"] == 0
        and len(first["streams"]) == 10,
        "generated_sha256": first["sha256"],
        "runtime_input_reads": first["runtime_input_file_reads"],
        "guarded_builds": 2,
        "identical_builds": first == second,
    }


def replay_original(base, row, report):
    slot = row["slot"]
    work = base / slot / "T01"
    freeze = loads(checked(work / "GenerationFreeze.json", row["freeze_sha256"], base))
    if (
        freeze["code_manifest_sha256"] != report["code_manifest_sha256"]
        or freeze["generated_sha256"] != row["generated_sha256"]
        or freeze["guarded_builds"] != 2
        or freeze["runtime_input_reads"] != 0
        or freeze["native_sources_read"] != 0
    ):
        raise ValueError("original freeze metadata differs")
    request = checked(work / "Request.json", freeze["request_sha256"], base)
    return {
        "slot": slot,
        "freeze_sha256": row["freeze_sha256"],
        "request_sha256": freeze["request_sha256"],
        **replay(request, row["generated_sha256"]),
    }


def original_base(root, report):
    method = loads(checked(root / "Method.json", report["method_sha256"], root))
    if (
        method["recipe_sha256"] != report["recipe_sha256"]
        or method["code_manifest_sha256"] != report["code_manifest_sha256"]
        or method["source_lock_sha256"] != report["source_lock_sha256"]
    ):
        raise ValueError("original method custody differs")
    recipe = loads(checked(root / "Recipe.json", report["recipe_sha256"], root))
    base = Path(recipe["guest_private_base"])
    if (
        not base.is_absolute()
        or len(base.drive) != 2
        or ".." in base.parts
        or recipe["frozen_code"]["writer_revision"] != report["writer_revision"]
    ):
        raise ValueError("private custody must remain guest local")
    resolved = base.resolve(strict=True)
    if resolved.drive != base.drive:
        raise ValueError("private custody must remain on its original drive")
    return resolved


def main():
    if os.name != "nt" or len(sys.argv) != 4:
        raise ValueError("digest-only comparison needs its frozen Windows context")
    original, disclosure, receipt = map(Path, sys.argv[1:])
    report = loads(checked(receipt, RECEIPT_SHA, receipt.parent))
    rows = report["originals"]
    if (
        report["schema"] != "kit.sw2026.offset-plane-original-native-acceptance.v1"
        or report["native_acceptance"] is not True
        or tuple(row["slot"] for row in rows) != ("H01", "H02")
        or any(row["passed"] is not True for row in rows)
    ):
        raise ValueError("original held-out acceptance custody differs")
    expected = report["windows_disclosed_qualification"]["generated_sha256"]
    d03_request = checked(disclosure / "Request.json", D03_REQUEST_SHA, disclosure)
    discriminator = replay(d03_request, expected)
    result = {
        "schema": "kit.sw2026.offset-plane-digest-regression.v1",
        "original_receipt_sha256": RECEIPT_SHA,
        "python": platform.python_version(),
        "python_exe_sha256": digest(Path(sys.executable).read_bytes()),
        "platform_machine": platform.machine(),
        "zlib_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "disclosed_windows_comparison": discriminator,
        "originals": [],
    }
    if discriminator["passed"]:
        base = original_base(original, report)
        result["originals"] = [replay_original(base, row, report) for row in rows]
    result["passed"] = discriminator["passed"] and all(
        row["passed"] for row in result["originals"]
    )
    print(dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    try:
        status = main()
    except Exception:
        print(dumps({"passed": False, "failure_code": "digest_replay_refused"}))
        status = 3
    raise SystemExit(status)
