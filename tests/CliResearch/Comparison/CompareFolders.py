from pathlib import Path as FilePath

from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import (
    ChangeSemantic,
    MakeDocument,
)


# codec exports provide a stable observable difference for installed comparison process checks
def CompareFolders(WorkPath: FilePath) -> tuple[FilePath, FilePath]:
    First, Second = WorkPath / "Left", WorkPath / "Right"
    First.mkdir()
    Second.mkdir()
    WriteDocument(First / "Part.json", MakeDocument("left"))
    WriteDocument(Second / "Part.json", ChangeSemantic(MakeDocument("right"), "role"))
    return First, Second
