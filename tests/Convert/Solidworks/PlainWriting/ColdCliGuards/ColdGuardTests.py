from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from os import pathsep as PathSeparator

from pytest import mark as TestMark, MonkeyPatch as PatchScope

from convert.api.ApiOpen import OpenDocument
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.ColdCliGuards.MakeColdGuard import (
    MakeColdGuard,
)
from tests.Convert.Solidworks.PlainWriting.ColdCliGuards.CheckColdError import (
    CheckColdError,
)
from tests.Convert.Solidworks.PlainWriting.MakeColdSource import MakeColdSource


# actual cli delegation must refuse forged or extended cold documents before changing any output
@TestMark.parametrize("RoleName", ("Skew", "Step"))
@TestMark.parametrize(
    "ModeName", ("fake", "binding", "feature", "metadata", "assembly", "embedded")
)
def CheckColdGuards(
    TmpPath: FilePath, RoleName: str, ModeName: str, MonkeyPatch: PatchScope
) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Source, Envelope, _, NameValue = MakeColdSource(TmpPath, RoleName)
    Changed = MakeColdGuard(OpenDocument(Source), ModeName, RoleName)
    Changed.AssertValid()
    assert IsColdRead(Changed)
    assert CadDocument.from_json(Changed.to_json()) == Changed
    InputPath = TmpPath / "ColdInput.json"
    Receipt = TmpPath / "Measurement.json"
    Target = TmpPath / NameValue
    _ = InputPath.write_text(Changed.to_json(), encoding="utf-8")
    assert IsColdRead(OpenDocument(InputPath))
    _ = Receipt.write_text(DumpJson(Envelope), encoding="utf-8")
    _ = Target.write_bytes(b"preserved output")
    BeforeSource, BeforeReceipt = Source.read_bytes(), Receipt.read_bytes()
    Outcome = CliProcess(
        TmpPath,
        "convert",
        str(InputPath),
        str(Target),
        "--overwrite",
        "--json",
        "--native-measurement",
        str(Receipt),
    )
    assert Outcome.returncode != 0 and "Traceback" not in Outcome.stderr
    CheckColdError(LoadJson(Outcome.stderr), ModeName)
    assert Target.read_bytes() == b"preserved output"
    assert Source.read_bytes() == BeforeSource and Receipt.read_bytes() == BeforeReceipt
    assert set(TmpPath.iterdir()) == {Source, InputPath, Receipt, Target}
