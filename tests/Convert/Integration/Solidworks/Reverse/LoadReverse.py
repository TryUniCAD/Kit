from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from tests.Convert.Integration.Solidworks.Reverse.ReverseCase import ReverseCase


# immutable independently generated archives keep the reader experiment separate from candidate construction
def LoadReverse(CaseName: str) -> ReverseCase:
    RootPath = FilePath(__file__).resolve().parents[5]
    StudyPath = RootPath / "re/solidworks/DecodedPromotion20261127"
    Report = LoadJson((StudyPath / "Evidence/Report.json").read_text())
    Sample = next(Value for Value in Report["cases"] if Value["case"] == CaseName)
    Source = StudyPath / "Evidence" / (CaseName + ".SLDPRT")
    assert HashBytes(Source.read_bytes()).hexdigest() == Sample["sha256"]
    Manifest = LoadJson((StudyPath / "Manifest.json").read_text())
    Member = next(
        Value
        for Value in Manifest["members"]
        if Value["path"] == "Evidence/" + Source.name
    )
    assert Member["sha256"] == Sample["sha256"]
    return ReverseCase(
        Source,
        Sample["semantic_input"]["reversed"],
        Sample["semantic_input"]["depth_mm"],
        Sample["expected_geometry"]["volume_mm3"],
        tuple(Sample["expected_geometry"]["centroid_mm"]),
        len(Sample["semantic_input"]["polygon_mm"]),
    )
