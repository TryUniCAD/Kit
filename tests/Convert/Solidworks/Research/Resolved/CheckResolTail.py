from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from tests.Convert.Solidworks.Research.ArchiveProcess import RunArchive
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Resolved.RunResolvedTool import RunResolvedTool


# opaque residual data must reject sdk admission even when legacy research can preserve its bytes
def CheckResolTail(InputPath: FilePath) -> None:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    StreamName = "Contents/Config-0-ResolvedFeatures"
    Streams = dict(Archive.streams)
    Streams[StreamName] = Archive.require(StreamName) + bytes(2)
    OutputPath = InputPath.with_stem("ResolvedWithTail")
    with OutputPath.open("xb") as Output:
        _ = Output.write(build_sldprt(Streams))
    SdkPath = OutputPath.with_suffix(".sdk.json")
    Rejected = RunResolvedTool("CheckSdkResolved.py", (OutputPath,), SdkPath)
    assert (
        Rejected.returncode != 0
        and "trailing bytes" in Rejected.stderr
        and not SdkPath.exists()
    )
    ReportPath = OutputPath.with_suffix(".research.json")
    Outcome = RunArchive(
        str(OutputPath),
        StreamName,
        ("--link-config", "--require-proven", "--report", str(ReportPath)),
    )
    assert Outcome.returncode != 0
    Report = ReadObject(ReportPath)
    assert Report["passed"] is False and Report["proven_schemas"] is False
    (FileValue,) = CastValue(list[dict[str, object]], Report["files"])
    Values = CastValue(dict[str, dict[str, object]], FileValue["streams"])[StreamName]
    assert Values["tail"] == 2 and Values["identical"] is True
    UsageValue = CastValue(dict[str, dict[str, object]], Values["schema_usage"])
    for Direction in ("load", "store"):
        Shared = CastValue(
            list[dict[str, object]], UsageValue[Direction]["shared_schema_usage"]
        )
        assert all(
            RowValue["admitted"] is False
            for RowValue in Shared
            if RowValue["codec"] == "sdk_ordinary_resolved"
        )
