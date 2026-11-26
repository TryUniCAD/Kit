import os as OsLib
import sys as System
from functools import partial as BindArguments
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from runpy import run_path as RunPath

from tests.Research.Archives.Comparison.BulkScanWitness import ScanWitness


# complete command execution must retain independent real entry telemetry even when discovery refuses
def RunObserved() -> None:
    TargetRoot = (FilePath.cwd() / "Left").resolve()
    CommandPath = (
        FilePath(__file__).resolve().parents[4] / "re/automation/CompareDecoded.py"
    )
    Counter = [0]
    setattr(System, "argv", [str(CommandPath), *System.argv[1:]])
    System.path.insert(0, str(CommandPath.parent))
    setattr(OsLib, "scandir", BindArguments(ScanWitness, TargetRoot, Counter))
    try:
        _ = RunPath(str(CommandPath), run_name="__main__")
    finally:
        print(EncodeJson({"witness": "bulk_scan", "consumed": Counter[0]}), flush=True)


if __name__ == "__main__":
    RunObserved()
