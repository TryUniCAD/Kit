from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.CliResearch.Comparison.CompareFolders import CompareFolders
from tests.CliResearch.ResearchClient import ResearchCli


# the installed launcher must preserve caller paths and the comparator report and difference status
@MarkValue.parametrize(
    "Pairing,RightUnit",
    (("relative_path", "mm"), ("manifest", "mm"), ("manifest", "cm")),
)
def CheckCompare(TmpPath: FilePath, Pairing: str, RightUnit: str) -> None:
    First, Second = CompareFolders(TmpPath)
    if Pairing == "manifest":
        Manifest = {
            "version": 1,
            "pairs": [
                {"id": "part", "left": "Left/Part.json", "right": "Right/Part.json"}
            ],
        }
        _ = (TmpPath / "Pairs.json").write_text(EncodeJson(Manifest), encoding="utf-8")
        Arguments = ("--manifest", "Pairs.json")
    else:
        Arguments = (First.name, Second.name)
    UnitFlags = (
        ("--unit", "mm")
        if RightUnit == "mm"
        else ("--left-unit", "mm", "--right-unit", RightUnit)
    )
    ExpectedPins = {
        SideName: HashBytes((Folder / "Part.json").read_bytes()).hexdigest()
        for SideName, Folder in (("left", First), ("right", Second))
    }
    Reply = ResearchCli(TmpPath, "compare", *Arguments, *UnitFlags, "-o", "Output")
    assert Reply.returncode == 2, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    assert Summary["exit_code"] == 2 and Summary["pairing"] == Pairing
    assert Summary["geometry_units"] == {"left": "mm", "right": RightUnit}
    assert Summary["outcomes"] == {"different": 1}
    PairRow = Summary["pairs"][0]
    assert PairRow["id"] == ("part" if Pairing == "manifest" else "Part.json")
    assert {
        SideName: PairRow["input_sha256"][SideName] for SideName in ExpectedPins
    } == ExpectedPins
    ReportBytes = (Output / PairRow["report"]["path"]).read_bytes()
    assert HashBytes(ReportBytes).hexdigest() == PairRow["report"]["sha256"]
    assert DecodeJson(ReportBytes)["status"] == "different"
    assert (Output / "summary.txt").is_file()
