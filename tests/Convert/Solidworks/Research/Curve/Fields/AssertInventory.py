from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Fields.AssertFieldCode import (
    AssertFieldCode,
)
from tests.Convert.Solidworks.Research.Curve.Fields.AssertFieldFile import (
    AssertFieldFile,
)


# full corpus membership prevents a partial inventory from appearing complete in retained artifacts
def AssertInventory(
    Report: dict[str, object],
    Entries: dict[str, dict[str, object]],
    StreamName: str,
    IsLinked: bool,
) -> dict[str, dict[str, int]]:
    assert Report["schema"] == "kit.sw2026.field-inventory.v1"
    assert Report["version"] == 19000
    assert Report["require_proven"] is Report["passed"] is True
    assert Report["linked_configurations"] is IsLinked
    assert Report["purpose"] == "discovery/control correlation of decoded model fields"
    assert (
        Report["integer_encoding"]
        == "exact JSON integer plus authoritative decimal text"
    )
    assert Report["scalar_type_scope"] == (
        "decoded Python values; no inferred native scalar wire width or field byte offset"
    )
    assert Report["graph_scope"] == (
        "retained document head, roots, loader context and archive map, "
        "plus explicit linked configuration graph"
    )
    assert Report["field_classification"] == (
        "unclassified; correlations are not construction rules or writer defaults"
    )
    for FlagName in (
        "raw_payloads_emitted",
        "values_truncated",
        "writer_output",
        "byte_roundtrip_performed",
    ):
        assert Report[FlagName] is False
    assert Report["native_acceptance"] == "unmeasured"
    AssertFieldCode(Report)
    Files = CastValue(list[dict[str, object]], Report["files"])
    Names = [FilePath(CastValue(str, FileData["path"])).name for FileData in Files]
    assert len(Files) == len(set(Names)) == Report["file_count"] == 26
    assert set(Names) == set(Entries)
    return {
        FileName: AssertFieldFile(FileData, Entries[FileName], StreamName, IsLinked)
        for FileName, FileData in zip(Names, Files, strict=True)
    }
