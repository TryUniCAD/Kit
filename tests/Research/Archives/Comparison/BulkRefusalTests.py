from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# rerunning a comparison must preserve the complete prior report instead of silently replacing evidence
def CheckOverwrite(TmpPath: FilePath) -> None:
    Document = TmpPath / "Document.json"
    WriteDocument(Document, MakeDocument())
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "one",
                        "left": "Document.json",
                        "right": "Document.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Output = TmpPath / "Output"
    Arguments = ["--manifest", str(Manifest), "--output", str(Output)]
    FirstRun = RunBulk(Arguments)
    assert FirstRun.returncode == 0, FirstRun.stderr + FirstRun.stdout
    Original = {
        Value: Value.read_bytes() for Value in Output.rglob("*") if Value.is_file()
    }
    SecondRun = RunBulk(Arguments)
    assert SecondRun.returncode == 1
    assert {Value: Value.read_bytes() for Value in Original} == Original


# bounded correspondence search must never turn an unfinished bulk comparison into equality
def CheckWorkBudget(TmpPath: FilePath) -> None:
    Document = TmpPath / "Document.json"
    WriteDocument(Document, MakeDocument())
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "one",
                        "left": "Document.json",
                        "right": "Document.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Output = TmpPath / "Output"
    Result = RunBulk(
        [
            "--manifest",
            str(Manifest),
            "--max-candidates",
            "1",
            "--output",
            str(Output),
        ]
    )
    assert Result.returncode == 3, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"incomplete": 1}


# sidecar receipts must be explicitly excluded when selecting decoder document directories
def CheckSelection(TmpPath: FilePath) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    for Folder in (First, Second):
        (Folder / "Case").mkdir(parents=True)
        WriteDocument(Folder / "Case/document.json", MakeDocument())
        assert (Folder / "Case/receipt.json").write_text("{}", encoding="utf-8") == 2
    Output = TmpPath / "Output"
    Result = RunBulk(
        [
            "--left",
            str(First),
            "--right",
            str(Second),
            "--pattern",
            "document.json",
            "--output",
            str(Output),
        ]
    )
    assert Result.returncode == 0, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["pair_count"] == 1
    assert Summary["pairs"][0]["id"] == "Case/document.json"


# output discovery must never become part of a later input comparison or modify source trees
def CheckOverlap(TmpPath: FilePath) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    First.mkdir()
    Second.mkdir()
    for Folder in (First, Second):
        WriteDocument(Folder / "Part.json", MakeDocument())
    Output = First / "Output"
    Result = RunBulk(
        [
            "--left",
            str(First),
            "--right",
            str(Second),
            "--output",
            str(Output),
        ]
    )
    assert Result.returncode == 1
    assert "outside" in Result.stderr
    assert not Output.exists()


# invalid usage cannot share the exit status reserved for completed observed differences
def CheckUsage(TmpPath: FilePath) -> None:
    Result = RunBulk(["--output", str(TmpPath / "Output"), "--left-unit", "invalid"])
    assert Result.returncode == 1
    assert "invalid choice" in Result.stderr
    assert not (TmpPath / "Output").exists()


# independently missing geometry contracts must refuse rather than silently assume display units
@MarkValue.parametrize(
    "GivenFlag,MissingFlag",
    (("--left-unit", "--right-unit"), ("--right-unit", "--left-unit")),
)
def CheckUnitFlags(TmpPath: FilePath, GivenFlag: str, MissingFlag: str) -> None:
    Result = RunBulk(
        [
            "--output",
            str(TmpPath / "Output"),
            GivenFlag,
            "mm",
        ],
        UseUnits=False,
    )
    assert Result.returncode == 1
    assert "required" in Result.stderr
    assert MissingFlag in Result.stderr
    assert not (TmpPath / "Output").exists()
