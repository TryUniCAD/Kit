from math import isclose as IsClose
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.PlainWriting.RunPlainCase import RunPlainCase

# different line counts distinguish dynamic resolved stream lengths under one document name
KPlainCases = (
    (((-14.0, -3.0), (23.0, 1.0), (4.0, 25.0)), 13.625, 6567.25),
    (
        (
            (-9.0, -7.0),
            (22.0, -7.0),
            (22.0, 14.0),
            (3.0, 14.0),
            (3.0, 5.0),
            (-9.0, 5.0),
        ),
        19.25,
        10452.75,
    ),
)


# file and stream output must preserve tip depth and line ownership through strict native readback
def TestPlainWriter() -> None:
    Sizes: list[int] = []
    for Corners, DepthValue, VolumeValue in KPlainCases:
        ReportValue = RunPlainCase(MakePlainDoc("QueuePlain", Corners, DepthValue))
        assert ReportValue["file_stream_equal"] is True
        assert ReportValue["target_file_opens"] == 1
        assert ReportValue["physical_destinations_intact"] is True
        assert ReportValue["explicit_windows_locator"] is True
        Refusals = CastValue(dict[str, str], ReportValue["refusals"])
        assert set(Refusals) == {
            "caller_stream_unnamed",
            "disconnected_loop",
            "overwrite_guard",
            "unknown_model_data",
            "unmodeled_configuration",
            "unsupported_extension",
            "unverified_strict_stream",
        }
        assert ReportValue["native_capabilities"] == [
            "body_structure",
            "configurations",
            "editable_sketches",
            "parameters",
            "parametric_history",
            "support_planes",
        ]
        for Boundary in ("path_readback", "stream_readback"):
            Readback = CastValue(dict[str, object], ReportValue[Boundary])
            assert Readback["tree_rows"] == Readback["linked_root_rows"] == 19
            assert Readback["line_count"] == len(Corners)
            assert Readback["driving_dimension"] == ["D1", "mm", DepthValue, True]
        Geometry = CastValue(dict[str, object], ReportValue["default_geometry"])
        SideCount = len(Corners)
        assert Geometry["topology"] == [
            1,
            1,
            SideCount + 2,
            3 * SideCount,
            2 * SideCount,
        ]
        assert Geometry["body_feature_linked"] is True
        assert IsClose(
            CastValue(float, Geometry["volume_mm3"]), VolumeValue, rel_tol=1e-12
        )
        assert ReportValue["raw_extraction_refusal"] == (
            "SLDPRT contains no readable Parasolid payload"
        )
        Lengths = CastValue(dict[str, int], ReportValue["logical_stream_lengths"])
        assert Lengths["Contents/Config-0"] > 0
        Sizes.append(Lengths["Contents/Config-0-ResolvedFeatures"])
    assert 0 < Sizes[0] < Sizes[1]
