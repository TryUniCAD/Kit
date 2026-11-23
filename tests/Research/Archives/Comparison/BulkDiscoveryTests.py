from json import loads as ParseJson
from os import R_OK as KReadFlag, X_OK as KExecFlag, access as HasAccess
from pathlib import Path as FilePath

from pytest import mark as MarkValue, skip as SkipCase

from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# real export folders keep discovery checks at the filesystem and command boundary
def MakeFolders(TmpPath: FilePath) -> tuple[FilePath, FilePath]:
    First = TmpPath / "Left"
    Second = TmpPath / "Right"
    First.mkdir()
    Second.mkdir()
    return First, Second


# unselected sidecars must consume the discovery budget before document evaluation starts
def CheckEntryLimit(TmpPath: FilePath) -> None:
    First, Second = MakeFolders(TmpPath)
    for Index in range(100000):
        (First / f"{Index:06d}.txt").touch()
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
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "input directory exceeds its discovery budget" in Result.stderr
    assert not Output.exists()
    assert len(tuple(First.iterdir())) == 100000


# streaming traversal must preserve deterministic pair ordering and leave sidecars unchanged
def CheckNestedScan(TmpPath: FilePath) -> None:
    First, Second = MakeFolders(TmpPath)
    for Folder in (First, Second):
        for CaseName in ("Zed", "Alpha"):
            CasePath = Folder / CaseName / "Nested"
            CasePath.mkdir(parents=True)
            WriteDocument(CasePath / "document.json", MakeDocument())
            _ = (CasePath / "receipt.json").write_text("{}", encoding="utf-8")
    Before = {
        Source: Source.read_bytes()
        for Folder in (First, Second)
        for Source in Folder.rglob("*.json")
    }
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
    assert [Entry["id"] for Entry in Summary["pairs"]] == [
        "Alpha/Nested/document.json",
        "Zed/Nested/document.json",
    ]
    assert Summary["outcomes"] == {"equal_observed_graph": 2}
    assert {Source: Source.read_bytes() for Source in Before} == Before


# selecting too many exports must refuse before reading or publishing any document
def CheckSelection(TmpPath: FilePath) -> None:
    First, Second = MakeFolders(TmpPath)
    for Index in range(1001):
        (First / f"{Index:04d}.json").touch()
    Output = TmpPath / "Output"
    Result = RunBulk(
        ["--left", str(First), "--right", str(Second), "--output", str(Output)]
    )
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "input directory exceeds 1000 selected files" in Result.stderr
    assert not Output.exists()
    assert len(tuple(First.iterdir())) == 1001


# linked inputs must fail before any output even when the link names a directory
@MarkValue.parametrize("IsDirectory", (False, True))
def CheckLinkedData(TmpPath: FilePath, IsDirectory: bool) -> None:
    First, Second = MakeFolders(TmpPath)
    TargetPath = TmpPath / "Target"
    if IsDirectory:
        TargetPath.mkdir()
    else:
        WriteDocument(TargetPath, MakeDocument())
    LinkPath = First / ("Linked" if IsDirectory else "Linked.json")
    try:
        LinkPath.symlink_to(TargetPath, target_is_directory=IsDirectory)
    except (NotImplementedError, OSError) as ErrorInfo:
        SkipCase(f"host cannot create the required symlink: {ErrorInfo}")
    Output = TmpPath / "Output"
    Result = RunBulk(
        ["--left", str(First), "--right", str(Second), "--output", str(Output)]
    )
    assert Result.returncode == 1, Result.stderr + Result.stdout
    Expected = "linked directory" if IsDirectory else "linked JSON file"
    assert Expected in Result.stderr
    assert not Output.exists()


# inaccessible descendants must refuse the complete batch rather than hide missing exports
def CheckDeniedScan(TmpPath: FilePath) -> None:
    First, Second = MakeFolders(TmpPath)
    BlockedPath = First / "Blocked"
    BlockedPath.mkdir()
    BlockedPath.chmod(0)
    Output = TmpPath / "Output"
    try:
        if HasAccess(BlockedPath, KReadFlag | KExecFlag):
            SkipCase("host permissions cannot make this directory inaccessible")
        Result = RunBulk(
            ["--left", str(First), "--right", str(Second), "--output", str(Output)]
        )
    finally:
        BlockedPath.chmod(0o700)
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "Permission denied" in Result.stderr
    assert not Output.exists()
