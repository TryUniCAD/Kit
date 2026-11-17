from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Frozen.FrameDelta import FrameDelta
from tests.Convert.Solidworks.Research.Frozen.MatchImports import MatchImports
from tests.Convert.Solidworks.Research.Frozen.ReadFrozen import ReadFrozen
from tests.Convert.Solidworks.Research.Frozen.RunPinned import RunPinned


# native receipts stay tied to exact historical bytes while the current frame correction is checked independently
def ComparePinned(
    Report: dict[str, object],
    Request: dict[str, object],
    SourceRoot: FilePath,
    IsCamera: bool,
) -> dict[str, object]:
    Manifest = ReadFrozen()
    Document = CastValue(dict[str, object], Request["document"])
    Expected = CastValue(dict[str, dict[str, object]], Manifest["measured_outputs"])[
        CastValue(str, Document["name"])
    ]
    Historical = RunPinned(Request, SourceRoot, IsCamera)
    MatchImports(Historical, SourceRoot)
    HistoricalBytes = DecodeBytes(CastValue(str, Historical["blob"]), validate=True)
    CurrentBytes = DecodeBytes(CastValue(str, Report["blob"]), validate=True)
    assert len(HistoricalBytes) == Expected["bytes"]
    assert HashBytes(HistoricalBytes).hexdigest() == Expected["sha256"]
    Changes = FrameDelta(
        CurrentBytes,
        HistoricalBytes,
        CastValue(str, Document["plane_axis"]),
        Report["profile_model_to_sketch"],
    )
    return {
        "source_revision": Manifest["source_revision"],
        "source_file_count": Manifest["source_file_count"],
        "measured_receipt": Expected["receipt"],
        "measured_sha256": Expected["sha256"],
        "historical_output_identical": True,
        "current_output_identical": CurrentBytes == HistoricalBytes,
        "changed_streams": Changes,
        "editable_project_imports": 0,
        "new_unseen_evidence": False,
        "native_acceptance_inherited": False,
    }
