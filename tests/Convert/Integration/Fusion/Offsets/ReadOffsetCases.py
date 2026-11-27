import json as JsonLib
from pathlib import Path as FilePath

from tests.Convert.Integration.Fusion.Offsets.OffsetCase import OffsetCase


# fixed native inputs prevent reader results from becoming their own expected values
def ReadOffsetCases() -> tuple[OffsetCase, ...]:
    RootPath = FilePath(__file__).resolve().parents[5]
    FixtureRoot = RootPath / "re/Fusion/OffsetAdmission20261127"
    Manifest = JsonLib.loads((FixtureRoot / "Manifest.json").read_text())
    Cases: list[OffsetCase] = []
    for Sample in Manifest["samples"]:
        Source = (FixtureRoot / Sample["file"]).resolve()
        if not Source.is_relative_to((FixtureRoot / "Controls").resolve()):
            raise ValueError("Native offset control escapes its recorded corpus")
        Cases.append(OffsetCase(Source, Sample["sha256"], Sample["observed"]))
    return tuple(Cases)
