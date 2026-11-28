from tests.Convert.Solidworks.Research.Drawing.Named.MakeNamedJob import MakeNamedJob
from tests.Convert.Solidworks.Research.Drawing.Named.RunNamedReject import (
    RunNamedReject,
)


# selector rotation and eligibility mismatches must be rejected independently by every admitted named family
def TestNamedFamily() -> None:
    for IndexValue, Orientation in enumerate(
        ("*Front", "*Top", "*Right", "*Isometric")
    ):
        JobValue = MakeNamedJob(
            "NamedFamily" + str(IndexValue),
            Orientation,
            0.71875,
            0.0349,
            0.0251,
            0.0123,
            0.13917,
            0.09683,
        )
        for ProbeName in ("selector", "basis", "eligibility"):
            RunNamedReject(JobValue, ProbeName)
