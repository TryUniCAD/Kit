from __future__ import annotations

from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.Fields.AssertFailFile import AssertFailFile
from tests.convert.solidworks.research.Curve.Fields.AssertFieldCode import (
    AssertFieldCode,
)


# failure reports must preserve complete input membership and honest source inventory scope
def AssertFailure(
    Report: dict[str, object],
    Expected: dict[str, str],
    Pattern: str,
    StreamName: str,
    FailureKind: str,
) -> None:
    assert Report["schema"] == "kit.sw2026.field-inventory.v1"
    assert Report["version"] == 19000
    assert Report["passed"] is False
    assert Report["require_proven"] is True
    assert Report["linked_configurations"] is False
    assert Report["writer_output"] is Report["raw_payloads_emitted"] is False
    assert Report["values_truncated"] is Report["byte_roundtrip_performed"] is False
    assert Report["native_acceptance"] == "unmeasured"
    AssertFieldCode(Report)
    Files = CastValue(list[dict[str, object]], Report["files"])
    Names = [CastValue(str, FileData["name"]) for FileData in Files]
    assert len(Files) == len(set(Names)) == Report["file_count"] == len(Expected)
    assert set(Names) == set(Expected)
    if FailureKind == "EmptyPattern":
        assert Report["error"] == "no input files matched"
    for FileData in Files:
        AssertFailFile(FileData, Expected, Pattern, StreamName, FailureKind)
