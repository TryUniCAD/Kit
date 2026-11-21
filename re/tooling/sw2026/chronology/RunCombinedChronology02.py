import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise ValueError("combined chronology output must be unused")
    output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.part-chronology-combined-proof.v1", "passed": False, "components": [], "heldout_inputs_read": 0, "native_processes": 0, "complete_original_source_preparation_admitted": False}
    try:
        for name, script in (("Chronology", "RunChronologyProof03.py"), ("Identity", "RunIdentityProof04.py")):
            result = subprocess.run([sys.executable, "-I", "-B", str(root / script), "--root", str(root), "--output", str(output / name)], capture_output=True, text=True, timeout=900)
            (output / (name + ".stdout.txt")).write_text(result.stdout)
            (output / (name + ".stderr.txt")).write_text(result.stderr)
            path = output / name / "Replay.json"
            if result.returncode or not path.is_file():
                raise RuntimeError("chronology component failed " + name + " " + result.stdout + result.stderr)
            value = json.loads(path.read_bytes())
            if not value["passed"] or value["heldout_inputs_read"] or value["native_processes"]:
                raise ValueError("chronology component did not satisfy the frozen boundary")
            report["components"].append({"name": name, "runner_sha256": sha256((root / script).read_bytes()).hexdigest(), "report_sha256": sha256(path.read_bytes()).hexdigest(), "fresh_processes": value["fresh_processes"]})
        report["passed"] = True
    except Exception as error:
        report["error"] = repr(error)
    finally:
        report["fresh_processes"] = sum(value["fresh_processes"] for value in report["components"])
        (output / "Combined.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
