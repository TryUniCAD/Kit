from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.CliResearch.Comparison.CompareFolders import CompareFolders
from tests.CliResearch.ResearchClient import ResearchCli


# incompatible syntax must fail before publication instead of silently choosing one option
@MarkValue.parametrize(
    "Arguments,Diagnostic",
    (
        (("Left", "Right"), "declare geometry units with --unit"),
        (
            ("Left", "Right", "--unit", "mm", "--left-unit", "cm"),
            "--unit cannot be combined",
        ),
        (
            ("Left", "Right", "--unit", "mm", "--right", "Right"),
            "supply exactly two folders",
        ),
        (
            ("Left", "Right", "--unit", "mm", "--manifest", "Pairs.json"),
            "supply exactly two folders",
        ),
        (("Left", "--unit", "mm"), "supply exactly two folders"),
    ),
)
def CheckBadCompare(
    TmpPath: FilePath, Arguments: tuple[str, ...], Diagnostic: str
) -> None:
    _ = CompareFolders(TmpPath)
    Reply = ResearchCli(TmpPath, "compare", *Arguments, "-o", "Output")
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    assert Diagnostic in Reply.stderr.splitlines()[-1]
    assert not (TmpPath / "Output").exists()


# help must remain accessible without export operands or a geometry declaration
def CheckHelp(TmpPath: FilePath) -> None:
    Reply = ResearchCli(TmpPath, "compare", "--help")
    assert Reply.returncode == 0, Reply.stderr
    assert all(
        Option in Reply.stdout for Option in ("FOLDER", "-o", "--unit", "--manifest")
    )
