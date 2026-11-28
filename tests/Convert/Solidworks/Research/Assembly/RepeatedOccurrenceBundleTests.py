from __future__ import annotations

from math import dist as VectorDistance, isclose as IsClose, sqrt as SquareRoot
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.AssemblyRootTests import KAssemblyRoots
from tests.Convert.Solidworks.Research.Assembly.OccurrenceArtifact import SaveOccBundle
from tests.Convert.Solidworks.Research.Assembly.OccurrenceAssertions import (
    CheckDirectory,
    CheckOccReport,
)
from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
from tests.Convert.Solidworks.Research.Assembly.RunRootProcess import RunRootProcess


# the third placement makes the native sphere merge sensitive to the traversal order
def MakeRepeatInput(NameValue: str) -> dict[str, object]:
    Request = MakeOccInput(NameValue, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
    Occurrences = CastValue(list[dict[str, object]], Request["occurrences"])
    Occurrences.extend(
        [
            {
                "name": "GeneratedChildModel-2",
                "placement": {
                    "origin": [0.1, -0.005, 0.0],
                    "u": [0.0, 1.0, 0.0],
                    "v": [-1.0, 0.0, 0.0],
                },
            },
            {
                "name": "GeneratedChildModel-3",
                "placement": {
                    "origin": [0.015, 0.045, 0.0],
                    "u": [1.0, 0.0, 0.0],
                    "v": [0.0, 1.0, 0.0],
                },
            },
        ]
    )
    return Request


# the reconstructed graph connects each occurrence to one shared child and its own context
def AssertTopology(
    Report: dict[str, object], ChildConfig: object, Occurrences: list[dict[str, object]]
) -> None:
    References = CastValue(list[dict[str, object]], Report["occurrences"])
    ConfigRows = CastValue(list[dict[str, object]], Report["occurrence_configurations"])
    assert len(References) == len(ConfigRows) == 3
    assert [Reference["name"] for Reference in References] == [
        Occurrence["name"] for Occurrence in Occurrences
    ]
    assert [Reference["ordinal"] for Reference in References] == list(
        range(len(KAssemblyRoots) - 1, len(KAssemblyRoots) + 2)
    )
    assert len({Reference["id"] for Reference in References}) == 3
    assert [ConfigRow["feature_id"] for ConfigRow in ConfigRows] == [
        Reference["id"] for Reference in reversed(References)
    ]
    for Reference, ConfigRow in zip(reversed(References), ConfigRows, strict=True):
        assert Reference["name"] == ConfigRow["name"]
        assert (
            Reference["child_configuration"]
            == ConfigRow["child_configuration"]
            == ChildConfig
        )
        assert Reference["directory_index"] == 0 and Reference["has_backlink"] is True
        assert ConfigRow["has_backlink"] is ConfigRow["has_serialized_owner"] is False
        assert ConfigRow["parent_identity_shared"] is True
    assert all(
        ConfigRow["parent_identity_slots"] == ConfigRows[0]["parent_identity_slots"]
        for ConfigRow in ConfigRows
    )
    ContextSlots = {
        MapSlot
        for ConfigRow in ConfigRows
        for MapSlot in CastValue(list[int], ConfigRow["record_slots"])
    }
    assert len(ContextSlots) == 21
    assert len({ConfigRow["name_handle_slot"] for ConfigRow in ConfigRows}) == 3
    assert all(
        Reference["local_bounds"] == References[0]["local_bounds"]
        for Reference in References
    )


# the first union tightens to its corner sphere and the last union keeps its shifted center
def AssertBounds(Report: dict[str, object]) -> None:
    FirstCenter = (0.050, 0.005, 0.0035)
    ThirdCenter = (0.025, 0.050, 0.0035)
    FirstRadius = SquareRoot(0.100**2 + 0.020**2 + 0.007**2) / 2
    ChildRadius = SquareRoot(0.020**2 + 0.010**2 + 0.007**2) / 2
    CenterDistance = VectorDistance(FirstCenter, ThirdCenter)
    ExpectedRadius = (FirstRadius + ChildRadius + CenterDistance) / 2
    Fraction = (ExpectedRadius - FirstRadius) / CenterDistance
    ExpectedCenter = tuple(
        Initial + Fraction * (Incoming - Initial)
        for Initial, Incoming in zip(FirstCenter, ThirdCenter, strict=True)
    )
    Expected = (*ExpectedCenter, 0.1, 0.055, 0.007, 0.0, -0.005, 0.0, ExpectedRadius)
    AssemblyBounds = CastValue(list[dict[str, float]], Report["bounds"])
    assert len(AssemblyBounds) == 2
    for Bounds in AssemblyBounds:
        assert all(
            IsClose(Bounds[f"b{Index}"], Value, abs_tol=1e-12)
            for Index, Value in enumerate(Expected)
        )


# repeated assembly output must decode completely through the same guarded process boundary
def TestRepeated() -> None:
    NameValue = "GeneratedRepeatAssembly"
    Request = MakeRepeatInput(NameValue)
    Report = RunRootProcess(Request)
    CheckOccReport(Report, OccurrenceCount=3)
    Occurrences = CastValue(list[dict[str, object]], Request["occurrences"])
    AssertTopology(Report, CheckDirectory(Report, OccurrenceCount=3), Occurrences)
    AssertBounds(Report)
    SaveOccBundle(NameValue, Request, Report)
