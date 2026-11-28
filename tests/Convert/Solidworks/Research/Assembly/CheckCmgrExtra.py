from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import RunArchive
from tests.Convert.Solidworks.Research.Assembly.MakeCmgrExtra import MakeCmgrExtra
from tests.Convert.Solidworks.Research.Assembly.RunCmgrCheck import RunCmgrCheck
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# research compatibility must never masquerade as successful shared sdk graph admission
def CheckCmgrExtra(ParentPath: FilePath) -> None:
    ExtendedPath = MakeCmgrExtra(ParentPath)
    RejectedPath = ExtendedPath.with_suffix(".sdk.json")
    Rejected = RunCmgrCheck((ExtendedPath,), RejectedPath)
    assert Rejected.returncode != 0 and "trailing bytes" in Rejected.stderr
    assert not RejectedPath.exists()
    ReportPath = ExtendedPath.with_suffix(".research.json")
    assert not ReportPath.exists()
    Outcome = RunArchive(
        str(ExtendedPath),
        "Contents/CMgr",
        ("--require-proven", "--report", str(ReportPath)),
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True and Report["byte_identity_passed"] is True
    (FileValue,) = CastValue(list[dict[str, object]], Report["files"])
    Streams = CastValue(dict[str, dict[str, object]], FileValue["streams"])
    UsageValue = CastValue(
        dict[str, dict[str, object]], Streams["Contents/CMgr"]["schema_usage"]
    )
    for Direction in ("load", "store"):
        assert UsageValue[Direction]["completed"] is True
        (Shared,) = CastValue(
            list[dict[str, object]], UsageValue[Direction]["shared_schema_usage"]
        )
        assert Shared["admitted"] is False and Shared["diagnostic"]
        assert CastValue(dict[str, object], Shared["usage"])["completed"] is False
