import json as JsonLib
from pathlib import Path as FilePath

from tests.Convert.Integration.Fusion.SpanCliCase import SpanCliCase


# pinned native measurements supply expected geometry without importing the production reader
def ReadSpanCases() -> tuple[SpanCliCase, ...]:
    RootPath = FilePath(__file__).resolve().parents[4]
    Manifest = JsonLib.loads(
        (RootPath / "re/Fusion/Reconstruction/CircularSpans/Manifest.json").read_text()
    )
    Results: list[SpanCliCase] = []
    for Sample in Manifest["samples"]:
        Source = (RootPath / Sample["file"]).resolve(strict=True)
        if not Source.is_relative_to(
            RootPath / "re/Fusion/Reconstruction/CircularSpans/Controls"
        ):
            raise ValueError("Native extent control escapes the recorded corpus")
        Bodies = Sample["observed"]["bodies"]
        if (
            len(Bodies) != 1
            or len(Bodies[0]["min_cm"]) != 3
            or len(Bodies[0]["max_cm"]) != 3
        ):
            raise ValueError("Native extent control has invalid measured geometry")
        BodyValue = Bodies[0]
        Results.append(
            SpanCliCase(
                Source,
                Sample["sha256"],
                Sample["side_mode"],
                float(BodyValue["volume_cm3"]) * 1000,
                float(BodyValue["area_cm2"]) * 100,
                tuple(float(Value) * 10 for Value in BodyValue["min_cm"]),
                tuple(float(Value) * 10 for Value in BodyValue["max_cm"]),
                len(Sample["observed"]["timeline"]),
                Sample["group"] + Sample["name"],
            )
        )
    return tuple(Results)
