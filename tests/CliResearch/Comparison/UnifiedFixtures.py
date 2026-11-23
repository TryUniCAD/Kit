from pathlib import Path as FilePath

from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument
from tests.Research.Archives.Comparison.SemanticDocuments import (
    ChangeSemantic,
    MakeDocument,
    MakeUnresolved,
    PermuteModel,
)


# different serialized identities expose whether agreement preserves the selected original bytes
def MakeInputs(WorkPath: FilePath, IncludeIssues: bool) -> dict[FilePath, bytes]:
    First, Second = WorkPath / "SolidWorks", WorkPath / "Fusion"
    First.mkdir()
    Second.mkdir()
    LeftEqual = First / "AEqual.json"
    WriteDocument(LeftEqual, MakeDocument("left"))
    _ = LeftEqual.write_bytes(LeftEqual.read_bytes() + b"\n \n")
    WriteDocument(Second / "AEqual.json", PermuteModel(MakeDocument("other")))
    if IncludeIssues:
        WriteDocument(First / "BChanged.json", MakeDocument())
        WriteDocument(Second / "BChanged.json", ChangeSemantic(MakeDocument(), "role"))
        Uncertain = MakeUnresolved("source_attributes")
        WriteDocument(First / "CUnresolved.json", Uncertain)
        WriteDocument(Second / "CUnresolved.json", Uncertain)
        WriteDocument(First / "DMissing.json", MakeDocument())
    return {
        InputPath: InputPath.read_bytes()
        for Folder in (First, Second)
        for InputPath in Folder.iterdir()
    }
