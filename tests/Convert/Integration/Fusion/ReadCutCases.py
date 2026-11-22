import json as JsonLib
from pathlib import Path as FilePath
from tests.Convert.Integration.Fusion.CutCliCase import CutCliCase


# captured expectations stay separate from every production decoding and geometry function
def ReadCutCases() -> tuple[CutCliCase, ...]:
    RootPath = FilePath(__file__).resolve().parents[4]
    Corpus = RootPath / "re/Fusion/Reconstruction/BoundaryCuts"
    Captures = JsonLib.loads((Corpus / "NativeObservations.json").read_text())[
        "controls"
    ]
    Captures.append(JsonLib.loads((Corpus / "RequestedCorner.json").read_text()))
    Results: list[CutCliCase] = []
    for Capture in Captures:
        if Capture["name"] in ("HealthyBefore", "HealthyAfter", "CornerPocket"):
            continue
        Bodies = Capture["observed"]["bodies"]
        Names = tuple(
            Value["name"]
            for Value in Capture["observed"]["parameters"]
            if Value["role"] == "AlongDistance"
        )
        if len(Bodies) != 1 or len(Names) != 2:
            raise ValueError("Native cut capture has ambiguous body or extent roles")
        BodyValue = Bodies[0]
        Source = (Corpus / "Controls" / Capture["file"]).resolve()
        if not Source.is_relative_to(Corpus / "Controls"):
            raise ValueError("Native cut capture escapes its source corpus")
        Results.append(
            CutCliCase(
                Source,
                Capture["sha256"],
                BodyValue["volume_cm3"] * 1000,
                BodyValue["area_cm2"] * 100,
                tuple(Value * 10 for Value in BodyValue["min_cm"]),
                tuple(Value * 10 for Value in BodyValue["max_cm"]),
                BodyValue["faces"],
                BodyValue["edges"],
                BodyValue["vertices"],
                tuple(Value["name"] for Value in Capture["observed"]["timeline"]),
                Names[0],
                Names[1],
            )
        )
    return tuple(Results)
