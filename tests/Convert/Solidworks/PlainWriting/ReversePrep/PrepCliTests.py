import json as JsonLib
from os import pathsep as PathSeparator
from pathlib import Path as FilePath

from pytest import mark as MarkTests, MonkeyPatch as PatchScope

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.ReversePrep.MakePrepDoc import MakePrepDoc
from tests.Convert.Solidworks.PlainWriting.ReversePrep.PrepCase import PrepCase
from tests.Convert.Solidworks.PlainWriting.ReversePrep.ReadPrepCases import (
    ReadPrepCases,
)


# ordinary conversion must require measured bytes even when reversed neutral preparation is complete
@MarkTests.parametrize(
    "CaseValue", tuple(Sample for Sample in ReadPrepCases() if Sample.IsReversed)
)
def CheckPrepCli(
    TmpPath: FilePath, CaseValue: PrepCase, MonkeyPatch: PatchScope
) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Source = TmpPath / "Neutral.json"
    Target = TmpPath / (CaseValue.NameValue + ".SLDPRT")
    _ = Source.write_text(MakePrepDoc(CaseValue).to_json(), encoding="utf-8")
    _ = Target.write_bytes(b"existing destination")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--json", "--overwrite"
    )
    assert Result.returncode != 0
    assert (
        "offline native measurement receipt" in JsonLib.loads(Result.stderr)["message"]
    )
    assert "Traceback" not in Result.stderr
    assert Target.read_bytes() == b"existing destination"
    assert set(TmpPath.iterdir()) == {Source, Target}
