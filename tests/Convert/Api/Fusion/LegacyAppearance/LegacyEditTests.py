from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.LegacyAppearance.CheckLegacy import CheckLegacy
from tests.Convert.Api.Fusion.LegacyAppearance.LegacyCase import LegacyCase
from tests.Convert.Api.Fusion.LegacyAppearance.RunLegacy import RunLegacy


# one requested scalar edit must preserve all other named and encoded values
def TestLegacyEdit(TmpPath: FilePath) -> None:
    Request = LegacyCase(TmpPath / "Request")
    First = TmpPath / "Before"
    First.mkdir()
    Result = RunLegacy(Request, First)
    assert Result.returncode == 0, Result.stderr
    Values = LoadJson(Request.read_text(encoding="utf-8"))
    Values["reflection_transmission"]["glossiness"] = 0.8125
    _ = Request.write_text(DumpJson(Values, allow_nan=False), encoding="utf-8")
    Second = TmpPath / "After"
    Second.mkdir()
    Result = RunLegacy(Request, Second)
    assert Result.returncode == 0, Result.stderr
    CheckLegacy(First)
    CheckLegacy(Second, 0.8125)
    assert (First / "Definition.bin").read_bytes() == (
        Second / "Definition.bin"
    ).read_bytes()
    assert (First / "Properties.bin").read_bytes() != (
        Second / "Properties.bin"
    ).read_bytes()
