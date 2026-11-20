from dataclasses import replace as ReplaceValue
from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Commands.BuildInactive import BuildInactive
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.Properties.WriteTextTests import KPartCause


# the portable geometry control reaches the text policy even with a selected configuration
def TestCliTextCopy(TmpPath: FilePath) -> None:
    Geometry = BuildInactive("Unordered")
    DocumentValue = ReplaceValue(
        Geometry,
        source=ReplaceValue(Geometry.source, format_id="solidworks.sldprt"),
        metadata={
            **Geometry.metadata,
            "solidworks.part_text_properties": {
                "status": "unsupported",
                "diagnostic": KPartCause,
            },
        },
    )
    SourcePath = TmpPath / "source.json"
    TargetPath = TmpPath / "target.json"
    Original = DocumentValue.to_json()
    _ = SourcePath.write_text(Original, encoding="utf-8")
    Args = ("convert", str(SourcePath), str(TargetPath), "--json")
    Copied = CliProcess(TmpPath, *Args)
    assert Copied.returncode == 0, Copied.stderr
    Output = TargetPath.read_bytes()
    assert LoadJson(Output) == LoadJson(Original)
    Filtered = CliProcess(
        TmpPath,
        *Args,
        "--configuration",
        DocumentValue.configurations[0].name,
        "--overwrite",
    )
    assert Filtered.returncode == 1 and Filtered.stdout == ""
    assert LoadJson(Filtered.stderr)["message"] == (
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})"
    )
    assert TargetPath.read_bytes() == Output
    assert SourcePath.read_text(encoding="utf-8") == Original
