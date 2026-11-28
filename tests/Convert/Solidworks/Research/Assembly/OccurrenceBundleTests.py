from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.OccurrenceArtifact import SaveOccBundle
from tests.Convert.Solidworks.Research.Assembly.OccurrenceAssertions import (
    CheckDirectory,
    CheckOccReport,
    CheckReference,
)
from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
from tests.Convert.Solidworks.Research.Assembly.OccurrencePlacement import (
    CheckPlacement,
)
from tests.Convert.Solidworks.Research.Assembly.RunRootProcess import RunRootProcess

# equally long names isolate the stream length change produced by the transform matrix
KPlacementCases = (
    (
        "GeneratedSingleAssembly",
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        (0.01, 0.005, 0.0035),
        (0.02, 0.01, 0.007),
        (0.0, 0.0, 0.0),
    ),
    (
        "GeneratedPlacedAssembly",
        [0.025, -0.012, 0.004],
        [0.0, 1.0, 0.0],
        [-1.0, 0.0, 0.0],
        (0.02, -0.002, 0.0075),
        (0.025, 0.008, 0.011),
        (0.015, -0.012, 0.004),
    ),
)


# the guarded subprocess must read back both generated files without runtime input reads
def TestOccurrence() -> None:
    Lengths: list[int] = []
    for (
        NameValue,
        Origin,
        AxisX,
        AxisY,
        Center,
        HighCorner,
        LowCorner,
    ) in KPlacementCases:
        Request = MakeOccInput(NameValue, Origin, AxisX, AxisY)
        Report = RunRootProcess(Request)
        CheckOccReport(Report)
        ChildConfig = CheckDirectory(Report)
        Reference = CheckReference(Report, ChildConfig)
        CheckPlacement(
            Report, Reference, Origin, AxisX, AxisY, Center, HighCorner, LowCorner
        )
        Lengths.append(CastValue(int, Report["root_bytes"]))
        SaveOccBundle(NameValue, Request, Report)
    assert Lengths[1] > Lengths[0] > 0
