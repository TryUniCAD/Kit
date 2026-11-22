from dataclasses import replace as ReplaceValue
from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Commands.BuildInactive import BuildInactive
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.Properties.WriteTextTests import KPartCause


# an otherwise portable cli source isolates the effects of native support and explicit property status
def TestCliTextCopy(TmpPath: FilePath) -> None:
    Geometry = BuildInactive("Unordered")
    SourcePath = TmpPath / "source.json"
    TargetPath = TmpPath / "target.json"
    Original = Geometry.to_json()
    _ = SourcePath.write_text(Original, encoding="utf-8")
    Arguments = ("convert", str(SourcePath), str(TargetPath), "--json")
    Copied = CliProcess(TmpPath, *Arguments)
    assert Copied.returncode == 0, Copied.stderr
    Output = TargetPath.read_bytes()
    assert LoadJson(Output) == LoadJson(Original)
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
    NativePath = TmpPath / "native-inspection.json"
    NativeJson = DocumentValue.to_json()
    _ = NativePath.write_text(NativeJson, encoding="utf-8")
    NativeArgs = ("convert", str(NativePath), str(TargetPath), "--json", "--overwrite")
    Unfiltered = CliProcess(TmpPath, *NativeArgs)
    assert Unfiltered.returncode == 1 and Unfiltered.stdout == ""
    Portability = LoadJson(Unfiltered.stderr)["message"]
    assert Portability.startswith("unqualified SOLIDWORKS sketch support references")
    assert Portability.endswith(": sketch")
    assert TargetPath.read_bytes() == Output
    Filtered = CliProcess(
        TmpPath, *NativeArgs, "--configuration", DocumentValue.configurations[0].name
    )
    assert Filtered.returncode == 1 and Filtered.stdout == ""
    assert LoadJson(Filtered.stderr)["message"] == (
        f"SOLIDWORKS part text properties are unavailable for writing ({KPartCause})"
    )
    assert TargetPath.read_bytes() == Output
    assert SourcePath.read_text(encoding="utf-8") == Original
    assert NativePath.read_text(encoding="utf-8") == NativeJson
