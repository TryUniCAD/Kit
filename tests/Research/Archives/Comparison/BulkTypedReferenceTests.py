from json import loads as ParseJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkValue

from interchange.serialization.JsonCodec import DumpJson
from tests.Research.Archives.Comparison.BulkOrderDocuments import MakeOrderDocs
from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.BulkTypedProcess import RunTypedBatch
from tests.Research.Archives.Comparison.BulkTypedDocuments import (
    LoseTypedRef,
    MakeCutDoc,
    MakeOffsetDoc,
    MakeOutputDoc,
)
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument


# independently named valid documents must align declared references while retaining intentional unknown face evidence
@MarkValue.parametrize("Family", ("outputs", "cut", "offset"))
def CheckTypedNames(TmpPath: FilePath, Family: str) -> None:
    First = (
        MakeOutputDoc("left")
        if Family == "outputs"
        else (
            MakeCutDoc("left", "same")
            if Family == "cut"
            else MakeOffsetDoc("left", "same")
        )
    )
    Second = (
        MakeOutputDoc("right")
        if Family == "outputs"
        else (
            MakeCutDoc("right", "same")
            if Family == "cut"
            else MakeOffsetDoc("right", "same")
        )
    )
    Report = RunTypedBatch(TmpPath, First, Second, 3 if Family == "offset" else 0)
    Comparison = CastValue(dict[str, object], Report["comparison"])
    assert Report["semantic_qualification"] == "unverified"
    assert Report["native_acceptance"] == "not_established"
    assert not Comparison["ambiguous"] and not Comparison["search_limited"]
    Matches = CastValue(list[dict[str, object]], Comparison["matches"])
    assert not any(Match["differences"] for Match in Matches)
    Issues = CastValue(list[dict[str, object]], Comparison["issues"])
    assert all(
        CastValue(dict[str, object], IssueItem["issue"])["reason"]
        != "unclassified_reference_semantics"
        for IssueItem in Issues
    )
    if Family == "offset":
        assert Report["status"] == "different" and Issues
        assert any(
            CastValue(dict[str, object], IssueItem["issue"])["reason"]
            == "unresolved_reference"
            for IssueItem in Issues
        )
    else:
        assert Report["status"] == "equal_observed_graph" and not Issues
        assert not Comparison["reference_differences"]


# actual operand changes must survive matching instead of being erased with document identifiers
@MarkValue.parametrize(
    "Family,Change,RoleName",
    (
        ("outputs", "target", "/OutputBodyIds/0"),
        ("cut", "target", "/definition/TargetBodyIds/0"),
        ("cut", "parameter", "/definition/Extrusion/AlongParameterId"),
        ("offset", "target", "/definition/TargetBodyId"),
        ("offset", "selection", "/definition/FaceSelectionId"),
        ("offset", "parameter", "/definition/DistanceParamId"),
    ),
)
def CheckTypedDiff(TmpPath: FilePath, Family: str, Change: str, RoleName: str) -> None:
    First = (
        MakeOutputDoc("left")
        if Family == "outputs"
        else (
            MakeCutDoc("left", "same")
            if Family == "cut"
            else MakeOffsetDoc("left", "same")
        )
    )
    Second = (
        MakeOutputDoc("right", True)
        if Family == "outputs"
        else (
            MakeCutDoc("right", Change)
            if Family == "cut"
            else MakeOffsetDoc("right", Change)
        )
    )
    Report = RunTypedBatch(TmpPath, First, Second, 3 if Family == "offset" else 2)
    assert Report["status"] == "different"
    Comparison = CastValue(dict[str, object], Report["comparison"])
    Differences = CastValue(
        list[dict[str, object]], Comparison["reference_differences"]
    )
    assert any(IssueItem["role"] == RoleName for IssueItem in Differences)
    assert not Comparison["ambiguous"] and not Comparison["search_limited"]


# order only changes must survive the real codec and bulk command without changing membership or scalar observations
@MarkValue.parametrize(
    "Family,RoleName",
    (
        ("outputs", "/OutputBodyIds"),
        ("cut_outputs", "/OutputBodyIds"),
        ("cut_targets", "/definition/TargetBodyIds"),
    ),
)
def CheckTypedOrder(TmpPath: FilePath, Family: str, RoleName: str) -> None:
    First, Second = MakeOrderDocs(Family)
    Report = RunTypedBatch(TmpPath, First, Second, 2)
    assert Report["status"] == "different"
    Comparison = CastValue(dict[str, object], Report["comparison"])
    Matches = CastValue(list[dict[str, object]], Comparison["matches"])
    assert not any(Match["differences"] for Match in Matches)
    Correspondence = {(Match["left"], Match["right"]) for Match in Matches}
    assert all(
        (BodyValue.id, BodyValue.id) in Correspondence for BodyValue in First.bodies
    )
    Differences = CastValue(
        list[dict[str, object]], Comparison["reference_differences"]
    )
    assert {Difference["role"] for Difference in Differences} == {
        RoleName + "/0",
        RoleName + "/1",
    }
    assert not Comparison["ambiguous"] and not Comparison["search_limited"]
    assert not Comparison["unmatched_left"] and not Comparison["unmatched_right"]
    assert not Comparison["issues"]
    assert Report["semantic_qualification"] == "unverified"
    assert Report["native_acceptance"] == "not_established"


# malformed typed links must fail at the real document admission boundary before graph matching
@MarkValue.parametrize(
    "Family,RoleName,Diagnostic",
    (
        (
            "outputs",
            "OutputBodyIds",
            "feature brokenboss references missing output body",
        ),
        (
            "cut",
            "TargetBodyIds",
            "distance cut brokenmodifier has missing sketch or body operands",
        ),
        (
            "offset",
            "TargetBodyId",
            "face offset brokenmodifier references a missing target body",
        ),
        (
            "offset",
            "FaceSelectionId",
            "face offset brokenmodifier is invalid: face offset requires one explicit face selection on its target body",
        ),
        (
            "offset",
            "DistanceParamId",
            "face offset brokenmodifier is invalid: unlinked or unowned extrusion parameter missing",
        ),
    ),
)
def CheckDangle(TmpPath: FilePath, Family: str, RoleName: str, Diagnostic: str) -> None:
    FirstPath = TmpPath / "Left"
    SecondPath = TmpPath / "Right"
    FirstPath.mkdir()
    SecondPath.mkdir()
    Document = (
        MakeOutputDoc("broken")
        if Family == "outputs"
        else (
            MakeCutDoc("broken", "same")
            if Family == "cut"
            else MakeOffsetDoc("broken", "same")
        )
    )
    WriteDocument(FirstPath / "Part.json", Document)
    Invalid = DumpJson(LoseTypedRef(Document, RoleName))
    assert (SecondPath / "Part.json").write_text(Invalid, encoding="utf-8") == len(
        Invalid
    )
    Output = TmpPath / "Output"
    Result = RunBulk(
        ["--left", str(FirstPath), "--right", str(SecondPath), "--output", str(Output)]
    )
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"reader_error": 1}
    Report = ParseJson(
        (Output / Summary["pairs"][0]["report"]["path"]).read_text(encoding="utf-8")
    )
    assert Report["status"] == "reader_error"
    assert Diagnostic in Report["reason"]
