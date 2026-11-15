from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.convert.solidworks.research.PolygonProcess import RunPolygon


def TestVariableN(TmpPath: FilePath) -> None:
    Sizes: list[int] = []
    for Count in (3, 5, 7):
        Outcome = RunPolygon(
            Directory=TmpPath, Scenario="ring", Count=Count, Depth=0.025
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = LoadJson(Outcome.stdout)
        assert Report["point_count"] == Report["line_count"] == Count
        assert Report["point_references"] and Report["line_references"]
        assert Report["point_creation_next"] == Count + 1
        assert Report["line_creation_next"] == Count + 1
        assert Report["marker_next"] == Count + 1
        assert Report["runtime_reads"] == []
        assert Report["module_read_count"] > 0
        assert not Report["vendor_loadable"] and not Report["application_usable"]
        Sizes.append(Report["stream_bytes"]["Research/Sketch"])
    assert Sizes[0] < Sizes[1] < Sizes[2]


def TestLargeRing(TmpPath: FilePath) -> None:
    Outcome = RunPolygon(Directory=TmpPath, Scenario="ring", Count=10000, Depth=0.125)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = LoadJson(Outcome.stdout)
    assert Report["point_count"] == Report["line_count"] == 10000
    assert Report["point_references"] and Report["line_references"]
    assert Report["runtime_reads"] == []


def TestBadRings(TmpPath: FilePath) -> None:
    for Scenario in ("crossing", "touch", "vertical_overlap", "backtrack"):
        Outcome = RunPolygon(Directory=TmpPath, Scenario=Scenario, Count=0, Depth=0.025)
        assert Outcome.returncode == 2, Outcome.stdout + Outcome.stderr
        Report = LoadJson(Outcome.stdout)
        assert Report["rejected"]
        assert Report["runtime_reads"] == []


def TestCollinear(TmpPath: FilePath) -> None:
    for Scenario, Count in (("collinear", 5), ("vertical", 6)):
        Outcome = RunPolygon(Directory=TmpPath, Scenario=Scenario, Count=0, Depth=0.025)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = LoadJson(Outcome.stdout)
        assert Report["point_count"] == Report["line_count"] == Count
        assert Report["point_references"] and Report["line_references"]


def TestDepthRefs(TmpPath: FilePath) -> None:
    Outcome = RunPolygon(Directory=TmpPath, Scenario="ring", Count=9, Depth=0.075)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = LoadJson(Outcome.stdout)
    assert Report["parameter_names"] == ["D1", "D2", "D3", "D4"]
    assert Report["parameter_ids"] == [-1] * 4
    FirstId = Report["expected_first_dimension_id"]
    assert Report["dimension_ids"] == list(range(FirstId, FirstId + 4))
    assert Report["next_persistent_id"] == FirstId + 5
    assert Report["from_offset_id"] == FirstId + 4
    assert Report["from_offset_name"] == "D19"
    assert Report["constructed_dimensions"] == 5
    assert Report["dimension_refcounts"] == [1] * 4
    assert Report["distinct_displays"] == 4
    assert Report["distinct_handles"] == 4
    assert Report["distinct_parameters"] == 4
    assert Report["edited_depth"] == 0.075 * 1.75
    assert Report["reverse_depth"] == 0.075
