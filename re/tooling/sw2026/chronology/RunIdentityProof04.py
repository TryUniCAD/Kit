import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from RunChronologyProof03 import require, verify, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "identity proof output must be unused")
    verify(root / "Source01.json", root / "Code01")
    verify(root / "Tools06.json", root / "Tools06")
    inputs_path = root / "IdentityInputs01.json"
    expected = "dc4c74b0844ef1b959eab084d11c11e63edced4e5930abcc014a9282a945c6fa"
    require(digest(inputs_path) == expected, "independent identity input bytes differ")
    inputs = json.loads(inputs_path.read_bytes())
    require(inputs["heldout_inputs_read"] == 0 and len(inputs["cases"]) == 2, "independent identity scope differs")
    output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.part-chronology-lower-identity-proof.v1", "passed": False, "source_manifest_sha256": digest(root / "Source01.json"), "tool_manifest_sha256": digest(root / "Tools06.json"), "input_manifest_sha256": digest(inputs_path), "runner_sha256": digest(Path(__file__)), "workers": [], "cases": [], "heldout_inputs_read": 0, "native_processes": 0, "complete_original_source_preparation_admitted": False}
    try:
        for index, row in enumerate(inputs["cases"]):
            name = "Identity" + str(index)
            result = subprocess.run([sys.executable, "-I", "-B", str(root / "Tools06/AuditPartIdentity03.py"), "--sdk", str(root / "Code01")], input=json.dumps(row).encode(), capture_output=True, timeout=90)
            (output / (name + ".stdout.json")).write_bytes(result.stdout)
            (output / (name + ".stderr.txt")).write_bytes(result.stderr)
            report["workers"].append({"name": name, "exit_code": result.returncode, "stdout_sha256": sha256(result.stdout).hexdigest(), "stderr_sha256": sha256(result.stderr).hexdigest()})
            require(result.returncode == 0, "identity worker failed " + name + " " + result.stderr.decode()[-2000:])
            value = json.loads(result.stdout)
            require(value["passed"] and not value["runtime_external_attempts"], "identity worker did not qualify its declared boundary")
            for path in value.pop("sdk_modules"):
                require(Path(path).is_relative_to(root / "Code01/src"), "identity SDK escaped the frozen source")
            report["cases"].append(value)
        verify(root / "Source01.json", root / "Code01")
        verify(root / "Tools06.json", root / "Tools06")
        report["passed"] = True
    except Exception as error:
        report["error"] = repr(error)
    finally:
        report["fresh_processes"] = len(report["workers"])
        (output / "Replay.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": report["passed"], "processes": report["fresh_processes"], "report_sha256": digest(output / "Replay.json"), "error": report.get("error")}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
