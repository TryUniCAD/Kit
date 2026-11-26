from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.LegacyAppearance.CheckLegacy import CheckLegacy
from tests.Convert.Api.Fusion.LegacyAppearance.LegacyCase import LegacyCase
from tests.Convert.Api.Fusion.LegacyAppearance.RunLegacy import RunLegacy


# independent fresh processes must reproduce complete authored groups from persisted input alone
def TestLegacyAgain(TmpPath: FilePath) -> None:
    Request = LegacyCase(TmpPath / "First")
    Original = Request.read_bytes()
    First = TmpPath / "FirstGroups"
    First.mkdir()
    Result = RunLegacy(Request, First)
    assert Result.returncode == 0, Result.stderr
    CheckLegacy(First)
    Repeat = TmpPath / "Repeat"
    Repeat.mkdir()
    Replayed = Repeat / "Request.json"
    _ = Replayed.write_bytes(Original)
    assert tuple(Repeat.iterdir()) == (Replayed,)
    Second = TmpPath / "SecondGroups"
    Second.mkdir()
    Result = RunLegacy(Replayed, Second)
    assert Result.returncode == 0, Result.stderr
    assert sorted(Entry.name for Entry in First.iterdir()) == [
        "Definition.bin",
        "Properties.bin",
    ]
    assert {Entry.name: Entry.read_bytes() for Entry in First.iterdir()} == {
        Entry.name: Entry.read_bytes() for Entry in Second.iterdir()
    }
    assert Request.read_bytes() == Replayed.read_bytes() == Original
