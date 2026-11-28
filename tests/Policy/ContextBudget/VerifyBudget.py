from pathlib import Path
from typing import cast as CastValue

from tests.Policy.ContextBudget.GitCommand import GitCommand


# each available snapshot must match its immutable git object including independent target changes
def VerifySnapshots(
    RootPath: Path,
    Context: dict[str, object],
    BeforeSha: str,
    HeadValue: str,
    TargetSha: str,
) -> None:
    Sources = CastValue(list[dict[str, object]], Context["files"])
    for Source in Sources:
        if "omitted" in Source:
            continue
        FileName = str(Source["path"])
        for FieldKey, Revision in (
            ("before", BeforeSha),
            ("after", HeadValue),
            ("target", TargetSha),
        ):
            assert Source[FieldKey] == GitCommand(
                RootPath, "show", Revision + ":" + FileName
            )


# total size and missing source gates remain separate from eliminating duplicate patch text
def VerifyBudget(CaseName: str, Context: dict[str, object], ContentSize: int) -> None:
    Sources = CastValue(list[dict[str, object]], Context["files"])
    assert ContentSize <= 900000
    assert Context["input_complete"] is (CaseName in ("small", "redundant"))
    if CaseName == "redundant":
        assert len(Sources) == 30 and any(Source["patch"] is None for Source in Sources)
        assert not any("omitted" in Source for Source in Sources)
    if CaseName == "small":
        assert all(isinstance(Source["patch"], str) for Source in Sources)
    if CaseName in ("binary", "oversized"):
        assert any("omitted" in Source for Source in Sources)
    if CaseName == "count":
        assert len(Sources) == 40 and Context["omitted_file_count"] == 1
