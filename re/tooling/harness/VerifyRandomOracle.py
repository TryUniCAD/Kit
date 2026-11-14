from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PureWindowsPath
import re
import subprocess


def Close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-6)


def Main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("expectations", type=Path)
    parser.add_argument("windows_root")
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    rows = []
    completed = set()
    partial_path = arguments.expectations.with_name("oracle-results-partial.json")
    if arguments.resume and partial_path.exists():
        rows = [
            row
            for row in json.loads(partial_path.read_text(encoding="utf-8"))
            if row.get("pass") is True
        ]
        completed = {row["label"] for row in rows}
        print(f"ORACLE_RESUMED={len(completed)}")
    for line in arguments.expectations.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 8:
            raise ValueError("invalid expectation row")
        label, depth, volume, area, com_x, com_y, com_z, filename = fields
        if label in completed:
            continue
        root = PureWindowsPath(arguments.windows_root)
        if root.drive != "Z:" or PureWindowsPath(filename).name != filename:
            raise ValueError("oracle paths must stay under the isolated Z research share")
        windows_path = arguments.windows_root.rstrip("\\") + "\\" + filename
        for attempt in (1, 2):
            try:
                result = subprocess.run(
                    [
                        "prlctl",
                        "exec",
                        "Windows 11",
                        "--current-user",
                        "cmd.exe",
                        "/c",
                        '"Z:\\Documents\\UniCAD\\Kit-solidworks-native\\.rescratch\\OracleLoadDiagnostics.exe" '
                        + f'"{windows_path}"',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                result = subprocess.CompletedProcess(
                    args=[], returncode=124, stdout="", stderr="oracle invocation timed out"
                )
                break
            if (
                "REVISION" in result.stdout
                or "PrlJob_" not in result.stdout + result.stderr
            ):
                break
        values = dict(re.findall(r"\b([A-Z][A-Z0-9_]*)=([^\s]+)", result.stdout))
        try:
            actual_com = tuple(
                float(value) for value in values.get("COM_MM", ",,").split(",")
            )
        except ValueError:
            actual_com = ()
        expected_com = (float(com_x), float(com_y), float(com_z))
        passed = (
            result.returncode == 0
            and values.get("LOAD_ERRORS") == "0"
            and values.get("LOAD_WARNINGS") == "0"
            and values.get("OPENED") == "True"
            and values.get("REBUILT") == "True"
            and values.get("BODIES") == "1"
            and Close(float(values.get("DEPTH_PARAMETER", "nan")), float(depth))
            and Close(float(values.get("VOLUME_MM3", "nan")), float(volume))
            and Close(float(values.get("AREA_MM2", "nan")), float(area))
            and len(actual_com) == 3
            and all(Close(actual, expected) for actual, expected in zip(actual_com, expected_com))
        )
        row = {
            "label": label,
            "file": filename,
            "pass": passed,
            "load_errors": values.get("LOAD_ERRORS"),
            "load_warnings": values.get("LOAD_WARNINGS"),
            "opened": values.get("OPENED"),
            "rebuilt": values.get("REBUILT"),
            "bodies": values.get("BODIES"),
            "depth_mm": values.get("DEPTH_PARAMETER"),
            "volume_mm3": values.get("VOLUME_MM3"),
            "area_mm2": values.get("AREA_MM2"),
            "com_mm": values.get("COM_MM"),
            "returncode": result.returncode,
            "attempts": attempt,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        rows.append(row)
        print(
            f"ORACLE_CASE={label} PASS={passed} ERRORS={values.get('LOAD_ERRORS')} "
            f"WARNINGS={values.get('LOAD_WARNINGS')} REBUILT={values.get('REBUILT')} "
            f"BODIES={values.get('BODIES')} VOLUME_MM3={values.get('VOLUME_MM3')} "
            f"AREA_MM2={values.get('AREA_MM2')} COM_MM={values.get('COM_MM')} "
            f"DEPTH={values.get('DEPTH_PARAMETER')}"
        )
        if not passed:
            partial_path.write_text(
                json.dumps(rows, indent=2) + "\n", encoding="utf-8"
            )
            return 3
    if len(rows) != 64:
        raise ValueError(f"expected 64 oracle results, received {len(rows)}")
    arguments.expectations.with_name("oracle-results.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )
    print(f"ORACLE_TOTAL={len(rows)} ORACLE_PASS={sum(row['pass'] for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
