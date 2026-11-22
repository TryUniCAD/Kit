from sys import platform as PlatformValue
from typing import cast as CastValue


# strict native transport retains all owners and requires complete binary identity before both publication routes
def AssertEqRead(Report: dict[str, object], Digest: str) -> None:
    IsMeasured = Report["sha256"] == Digest
    assert Report["matches_measured_archive"] is IsMeasured
    assert Report["published_routes"] == (
        (4 if PlatformValue == "win32" else 5) if IsMeasured else 0
    )
    assert Report["feature_rows"] == 19
    assert Report["parameter_ids"] == [
        "sldprt:parameter:18:D1",
        "sldprt:parameter:18:D2",
        "sldprt:parameter:21:D1",
    ]
    assert Report["width_inverse"] == {
        "width_mm": 20.01,
        "depth_mm": 10.005,
        "strict_readback_regenerated": True,
        "publication_refused": True,
    }
    Refusals = CastValue(list[str], Report["refusals"])
    assert "unqualified_mode_partial_diagnostic" in Refusals
    assert "unqualified_mode_raw_diagnostic" in Refusals
