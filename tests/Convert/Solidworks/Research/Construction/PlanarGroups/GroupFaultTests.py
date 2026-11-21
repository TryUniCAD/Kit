from pathlib import Path
import json
import subprocess
import sys
from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupFaultCase import (
    GroupFaultCase,
)


# complete process rejection must publish no candidate bytes for unsupported ownership geometry state or reference families
def TestGroupFails() -> None:
    RootValue = Path(__file__).resolve().parents[6]
    for FaultValue in (
        "missing_endpoint",
        "same_occurrence",
        "cross_axis",
        "same_name",
        "zero_distance",
        "wrong_distance",
        "fixed_missing",
        "extra_state",
    ):
        RequestValue = GroupFaultCase(FaultValue)
        ResultValue = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(RootValue / "re/tooling/sw2026/SdkPlanarGroupProcess.py"),
                str(RootValue),
            ],
            input=json.dumps(RequestValue, allow_nan=False),
            text=True,
            capture_output=True,
            timeout=120,
        )
        assert ResultValue.returncode != 0
        assert ResultValue.stdout == ""
        assert "ValueError" in ResultValue.stderr
        assert "PermissionError" not in ResultValue.stderr
