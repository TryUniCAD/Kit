from __future__ import annotations

from math import isclose as IsClose, radians as Radians
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.Revolve.RevolveInput import MakeRevolve


# compare generated archives at the isolated file boundary across two planes and directions
def TestRevolvePart() -> None:
    FullReport = RunFreshPart(MakeRevolve("z", "round", 360.0, False))
    ReverseReport = RunFreshPart(
        MakeRevolve("y", "long requested feature name " * 19, 147.5, True)
    )
    for Report, Degrees, Direction in (
        (FullReport, 360.0, 0),
        (ReverseReport, 147.5, 1),
    ):
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert all(
            Stream["passed"] and Stream["tail"] == 0 for Stream in Streams.values()
        )
        assert Report["denied_reads"] == []
        assert Report["points"] == 6 and Report["lines"] == 5
        assert Report["depth"] is None and Report["has_extrusion"] is False
        assert CastValue(list[str], Report["features"])[-2:] == [
            "moProfileFeature_c",
            "moRevolution_c",
        ]
        Readback = CastValue(dict[str, object], Report["revolution"])
        assert Readback["angle_rad"] == Readback["cached_angle_rad"] == Radians(Degrees)
        assert Readback["mode"] == Readback["end_condition"] == 0
        assert Readback["reverse"] == Direction and Readback["single_end"] == 1
        assert Readback["profile_owned"] is True
        assert (
            Readback["profile_reference_id"] == Readback["profile_id"]
            and Readback["profile_reference_time"] == 2592000
        )
        assert Readback["selected_line_id"] == 4
        assert Readback["axis_mark"] == Readback["line_mark"]
        assert (
            Readback["axis_record_flags"] == 2 and Readback["axis_entity_flags"] == 12
        )
        assert IsClose(CastValue(float, Readback["axis_length"]), 0.074, abs_tol=1e-14)
        assert (
            Readback["legacy_displays_absent"]
            is Readback["reverse_display_absent"]
            is True
        )
        assert Readback["converted_displays"] == 0
        assert Readback["keyword_angle"] == f"{Degrees:g}°"
        assert Readback["keyword_frame"] is True
        assert Readback["keyword_feature_id"] == Readback["feature_id"]
        assert Readback["keyword_axis_profile"] == {
            "Dissectable": "true",
            "Name": "Sketch1",
            "id": str(Readback["profile_id"]),
        }
    assert CastValue(dict[str, object], FullReport["revolution"])["axis_start"] == {
        "x": -0.006,
        "y": -0.033,
        "z": 0.0,
    }
    assert CastValue(dict[str, object], ReverseReport["revolution"])["axis_start"] == {
        "x": -0.006,
        "y": 0.0,
        "z": 0.033,
    }
    assert CastValue(dict[str, object], ReverseReport["revolution"])[
        "axis_direction"
    ] == {
        "x": 0.0,
        "y": 0.0,
        "z": -1.0,
    }
    assert (
        CastValue(dict[str, int], ReverseReport["sizes"])[
            "Contents/Config-0-ResolvedFeatures"
        ]
        > CastValue(dict[str, int], FullReport["sizes"])[
            "Contents/Config-0-ResolvedFeatures"
        ]
    )
