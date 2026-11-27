from json import loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import (
    ChangeSemantic,
    MakeDocument,
    MakeSymmetric,
    MakeUnresolved,
    PermuteModel,
)


# one invalid export must not hide valid matches differences or missing counterparts
def CheckMixedBatch(TmpPath: FilePath) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    Output = TmpPath / "Output"
    First.mkdir()
    Second.mkdir()
    WriteDocument(First / "Equal.json", MakeDocument())
    WriteDocument(Second / "Equal.json", PermuteModel(MakeDocument("other")))
    WriteDocument(First / "Changed.json", MakeDocument())
    WriteDocument(Second / "Changed.json", ChangeSemantic(MakeDocument(), "role"))
    WriteDocument(First / "Missing.json", MakeDocument())
    assert (First / "AInvalid.json").write_text("{}", encoding="utf-8") == 2
    WriteDocument(Second / "AInvalid.json", MakeDocument())
    Before = {PathName: PathName.read_bytes() for PathName in First.glob("*.json")}
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
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["pair_count"] == 4
    assert Summary["outcomes"] == {
        "equal_observed_graph": 1,
        "different": 1,
        "missing_input": 1,
        "reader_error": 1,
    }
    assert Summary["semantic_qualification"] == "unverified"
    assert Summary["native_acceptance"] == "not_established"
    assert Summary["pairs"][0]["status"] == "reader_error"
    EqualRow = next(Value for Value in Summary["pairs"] if Value["id"] == "Equal.json")
    assert EqualRow["counts"]["matched_features"] == 2
    Report = ParseJson(
        (Output / EqualRow["report"]["path"]).read_text(encoding="utf-8")
    )
    assert Report["comparison"]["matches"]
    assert Report["input_sha256"]["left"] != Report["input_sha256"]["right"]
    assert "Equal.json" in (Output / "summary.txt").read_text(encoding="utf-8")
    assert {PathName: PathName.read_bytes() for PathName in Before} == Before


# ambiguous graph identities must remain unresolved when processing a whole export folder
def CheckAmbigBatch(TmpPath: FilePath) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    First.mkdir()
    Second.mkdir()
    WriteDocument(First / "Symmetric.json", MakeSymmetric())
    WriteDocument(Second / "Symmetric.json", MakeSymmetric())
    Output = TmpPath / "Output"
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
    assert Result.returncode == 3, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"ambiguous": 1}
    assert Summary["pairs"][0]["counts"]["ambiguous"] > 0


# isolated outcome batches preserve difference and unresolved exit meanings outside mixed error batches
@MarkValue.parametrize(
    "Scenario,ExitCode,StatusName",
    (
        ("different", 2, "different"),
        ("unresolved", 3, "unresolved"),
        ("different_unresolved", 3, "different"),
    ),
)
def CheckOutcomes(
    TmpPath: FilePath, Scenario: str, ExitCode: int, StatusName: str
) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    First.mkdir()
    Second.mkdir()
    Document = (
        MakeUnresolved("source_attributes")
        if "unresolved" in Scenario
        else MakeDocument()
    )
    WriteDocument(First / "Part.json", Document)
    WriteDocument(
        Second / "Part.json",
        (
            ChangeSemantic(Document, "role")
            if Scenario.startswith("different")
            else Document
        ),
    )
    Output = TmpPath / "Output"
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
    assert Result.returncode == ExitCode, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {StatusName: 1}
    if "unresolved" in Scenario:
        assert Summary["pairs"][0]["counts"]["source_issues"] > 0


# input failures must outrank retained source uncertainty without hiding later comparisons or their detailed evidence
@MarkValue.parametrize("StatusName", ("unresolved", "different"))
def CheckErrorFirst(TmpPath: FilePath, StatusName: str) -> None:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    Output = TmpPath / "Output"
    First.mkdir()
    Second.mkdir()
    Document = MakeUnresolved("source_attributes")
    assert (First / "AInvalid.json").write_text("{}", encoding="utf-8") == 2
    WriteDocument(Second / "AInvalid.json", MakeDocument())
    WriteDocument(First / "Part.json", Document)
    WriteDocument(
        Second / "Part.json",
        ChangeSemantic(Document, "role") if StatusName == "different" else Document,
    )
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
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["pair_count"] == 2
    assert Summary["exit_code"] == 1
    assert Summary["outcomes"] == {"reader_error": 1, StatusName: 1}
    assert Summary["pairs"][0]["status"] == "reader_error"
    LaterRow = Summary["pairs"][1]
    assert LaterRow["id"] == "Part.json"
    assert LaterRow["status"] == StatusName
    assert LaterRow["counts"]["source_issues"] > 0
    Report = ParseJson(
        (Output / LaterRow["report"]["path"]).read_text(encoding="utf-8")
    )
    assert Report["status"] == StatusName
    assert all(Source["unresolved"] for Source in Report["sources"].values())
