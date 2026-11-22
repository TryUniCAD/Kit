from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from os import name as KOsName
from pathlib import Path as FilePath, PureWindowsPath

from tests.Convert.Commands.CliProcess import CliProcess


# the installed command enforces the native locator before publishing a measured bundle
def TestNestedCli(TmpPath: FilePath) -> None:
    FixtureValue = LoadJson(
        FilePath(__file__)
        .with_name("MeasuredDimensionedBundle.json")
        .read_text(encoding="utf-8")
    )
    Source = TmpPath / "Neutral.json"
    Receipt = TmpPath / "Measurement.json"
    _ = Source.write_text(DumpJson(FixtureValue["neutral"]), encoding="utf-8")
    _ = Receipt.write_text(DumpJson(FixtureValue["measurement"]), encoding="utf-8")
    NativePath = PureWindowsPath(FixtureValue["native_destination"])
    Target = TmpPath / NativePath.name
    CommandArgs = (
        "convert",
        str(Source),
        str(Target),
        "--json",
        "--native-measurement",
        str(Receipt),
        "--native-destination",
    )
    Wrong = CliProcess(
        TmpPath, *CommandArgs, str(NativePath.parent / "Other" / NativePath.name)
    )
    ExpectedText = (
        "must match the final Windows destination" if KOsName == "nt" else "namespace"
    )
    assert (
        Wrong.returncode == 1
        and not Wrong.stdout
        and ExpectedText in LoadJson(Wrong.stderr)["message"]
        and set(TmpPath.iterdir()) == {Source, Receipt}
    )
    if KOsName == "nt":
        return
    Result = CliProcess(TmpPath, *CommandArgs, str(NativePath))
    assert Result.returncode == 0 and not Result.stderr, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["application_usable"] is Report["vendor_loadable"] is True
    assert Report["dropped"] == []
    assert {
        Member.name: CalcSha(Member.read_bytes()).hexdigest()
        for Member in set(TmpPath.iterdir()) - {Source, Receipt}
    } == {
        MemberRow["name"]: MemberRow["sha256"]
        for MemberRow in FixtureValue["measurement"]["receipt"]["members"]
    }
