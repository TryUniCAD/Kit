import json as JsonLib
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.ReversePrep.PrepCase import PrepCase


# committed independent requests and analytic outcomes must drive complete archive integration checks
def ReadPrepCases() -> tuple[PrepCase, ...]:
    RootPath = FilePath(__file__).resolve().parents[5]
    Report = JsonLib.loads(
        (
            RootPath / "re/solidworks/DecodedPromotion20261127/Evidence/Report.json"
        ).read_text()
    )
    return tuple(
        PrepCase(
            CaseRow["case"],
            tuple(
                CastValue(tuple[float, float], tuple(Point))
                for Point in CaseRow["semantic_input"]["polygon_mm"]
            ),
            CaseRow["semantic_input"]["depth_mm"],
            CaseRow["semantic_input"]["reversed"],
            CaseRow["expected_geometry"]["volume_mm3"],
            CastValue(
                tuple[float, float, float],
                tuple(CaseRow["expected_geometry"]["centroid_mm"]),
            ),
        )
        for CaseRow in Report["cases"]
    )
